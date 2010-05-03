from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
from datetime import *
import re

FTV_PREFIX     = '/video/foratv_r2'
FTV_ROOT       = 'http://fora.tv'
LLNW_ROOT      = 'rtmp://foratv.fcod.llnwd.net/a953/o10'
FTV_TOPICS     = ['Economy', 'Environment', 'Politics', 'Science', 'Technology', 'Culture']
FTV_PLAYER     = '/fora/fora_player_full?cid=%s&h=0&b=0&p=FORA_Player_5&r=Other/Unrecognized'
CACHE_INTERVAL = 3600 * 6
MAX_ITEMS      = 40
MOST_WINDOW    = 14

def Start():
  Plugin.AddPrefixHandler(FTV_PREFIX, MainMenu, 'FORA.tv', 'icon-default.png', 'art-default.png')
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
  Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
  MediaContainer.title1 = 'FORA.tv'
  MediaContainer.content = 'items'
  MediaContainer.art = R('art-default.png')
  DirectoryItem.thumb = R('icon-default.png')
  HTTP.SetCacheTime(CACHE_INTERVAL)

def UpdateCache():
  HTTP.Request(FTV_ROOT)

def MainMenu():
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(FeaturedMenu, title="Featured")))
  dir.Append(Function(DirectoryItem(TopicMenu, title="By Topic")))
  dir.Append(Function(DirectoryItem(MostMenu, title="Week's Most Watched"), choice='views'))
  dir.Append(Function(DirectoryItem(MostMenu, title="Week's Most Commented"), choice='comments'))
  dir.Append(Function(SearchDirectoryItem(SearchMenu, thumb=R('icon-default.png'), title='Search FORA.tv', prompt='Search FORA.tv')))
  return dir

def FeaturedMenu(sender, choice=''):
  dir = MediaContainer(viewGroup='InfoList', title2=sender.itemTitle if choice == '' else choice)
  doc = XML.ElementFromURL(FTV_ROOT if choice == '' else FTV_ROOT+'/topic/'+choice, True)
  cinema = doc.xpath('//div[@class and contains(concat(" ",normalize-space(@class)," "), " common_cinema ")]')[0]
  title = cinema.xpath('.//div[@class="cinema_content"]/h2/a')[0].text
  href = cinema.xpath('.//div[@class="cinema_content"]/h2/a')[0].get('href')
  key = href[0:href.find('#')]
  thumb = cinema.xpath('.//a[@class="cinema_image"]/img')[0].get('src')
  subtitle = cinema.xpath('.//div[@class="l_partner"]/a')[0].text
  summary = cinema.xpath('.//div[@class="cinema_content"]/h3')[0].text.strip()
  dir.Append(Function(RTMPVideoItem(PlayForaVideo, title=title, subtitle=subtitle, summary=summary, thumb=FTV_ROOT+thumb), url=FTV_ROOT+key))
  for e in doc.xpath('//div[@class="featured_bit"]'):
    title = e.xpath('.//div[@class="featured_title"]/a')[0].text
    href = e.xpath('.//a')[0].get('href')
    key = href[0:href.find('#')]
    thumb = e.xpath('.//a/img')[0].get('src')
    subtitle = e.xpath('.//div[@class="l_partner"]/a')[0].text
    dir.Append(Function(RTMPVideoItem(PlayForaVideo, title=title, subtitle=subtitle, thumb=FTV_ROOT+thumb), url=FTV_ROOT+key))
  return dir

def TopicMenu(sender, choice=''):
  dir = MediaContainer(viewGroup='List', title2=choice.split('/')[0].title())
  if choice == '':
    for topic in FTV_TOPICS:
      dir.Append(Function(DirectoryItem(TopicMenu, title=topic), choice=topic))
  elif choice in FTV_TOPICS:
    dir.Append(Function(DirectoryItem(FeaturedMenu, title="Featured"), choice=choice))
    dir.Append(Function(DirectoryItem(TopicMenu, title="Most Recent"), choice=choice.lower()+'/all'))
    dir.Append(Function(DirectoryItem(MostMenu, title="Week's Most Watched"), choice='views', topic=choice.lower()))
    dir.Append(Function(DirectoryItem(MostMenu, title="Week's Most Commented"), choice='comments', topic=choice.lower()))
  else:
    dir.viewGroup = 'InfoList'
    for e in XML.ElementFromURL(FTV_ROOT+'/topic/'+choice, True).xpath('//div[@class="featured_bit"]'):
      title = e.xpath('.//div[@class="featured_title"]/a')[0].text
      href = e.xpath('.//div[@class="featured_title"]/a')[0].get('href')
      key = href[0:href.find('#')]
      thumb = e.xpath('.//div[@class="cropped_image"]')[0].get('style')
      subtitle = e.xpath('.//div[@class="l_partner"]/a')[0].text
      summary = 'Views: %s\nComments: %s' % (e.xpath('.//span[@class="views"]')[0].text, e.xpath('.//span[@class="views"]')[1].text)
      dir.Append(Function(RTMPVideoItem(PlayForaVideo, title=title, subtitle=subtitle, summary=summary, thumb=FTV_ROOT+thumb[thumb.find('(')+1:thumb.find(')')]), url=FTV_ROOT+key))
  return dir

def MostMenu(sender, choice, topic=''):
  dir = MediaContainer(viewGroup='InfoList', title2=sender.itemTitle)
  res = []
  keys = []
  tops = map(str.lower, FTV_TOPICS) if topic == '' else [topic]
  for topic in tops:
    #for e in XML.ElementFromURL('%s/topic/%s/all?sort=%s' % (FTV_ROOT, topic, choice), True).xpath('//div[@class="featured_bit"]'):
    for e in XML.ElementFromURL('%s/topic/%s/all' % (FTV_ROOT, topic), True).xpath('//div[@class="featured_bit"]'):
      title = e.xpath('.//div[@class="featured_title"]/a')[0].text
      href = e.xpath('.//div[@class="featured_title"]/a')[0].get('href')
      key = href[0:href.find('#')]
      thumb = e.xpath('.//div[@class="cropped_image"]')[0].get('style')
      subtitle = e.xpath('.//div[@class="l_partner"]/a')[0].text
      c = int(e.xpath('.//span[@class="views"]')[0 if choice == 'views' else 1].text.replace(',', ''))
      if key not in keys:
        (y,m,d) = map(int, key.split('/')[1:4])
        if datetime.now()-timedelta(days=MOST_WINDOW) < datetime(y,m,d):
          keys += [key]
          res += [(c, key, title, subtitle, thumb, topic)]
  sres = sorted(res, key=lambda t: t[0])
  sres.reverse()
  for item in sres[:min(MAX_ITEMS, len(sres))]:
    dir.Append(Function(RTMPVideoItem(PlayForaVideo, title=item[2], subtitle=item[3], summary=item[5].title()+'\n'+str(item[0])+(' Views' if choice == 'views' else ' Comments'), thumb=FTV_ROOT+item[4][item[4].find('(')+1:item[4].find(')')]), url=FTV_ROOT+item[1]))
  return dir

def SearchMenu(sender, query):
  dir = MediaContainer(viewGroup='InfoList', title2=query)
  for e in XML.ElementFromURL(FTV_ROOT+'/search_video?q=%s&per_page=%s' % (String.Quote(query), MAX_ITEMS), True).xpath('//div[@class="clip_bit "]'):
    title = e.xpath('.//a[@class="clip_bit_title"]')[0].text
    href = e.xpath('.//a[@class="cropped_thumb"]')[0].get('href')
    key = href[0:href.find('#')]
    thumb = e.xpath('.//a[@class="cropped_thumb"]/img')[0].get('src')
    subtitle = e.xpath('.//div[@class="l_partner"]/a')[0].text
    summary = 'Views: %s\nComments: %s' % (e.xpath('.//span[@class="views"]')[0].text, e.xpath('.//span[@class="views"]')[1].text)
    dir.Append(Function(RTMPVideoItem(PlayForaVideo, title=title, subtitle=subtitle, summary=summary, thumb=FTV_ROOT+thumb), url=FTV_ROOT+key))
  return dir

def PlayForaVideo(sender, url):
  page = HTTP.Request(url)
  clipid = re.search('var full_program_clipid = (.+?);', page, re.DOTALL).group(1)
  doc = XML.ElementFromURL(FTV_ROOT+FTV_PLAYER % clipid, True)
  clip = re.search('^(.*)(\.flv)$', doc.xpath('//playerdata/encodeinfo/encode_url')[0].text, re.DOTALL).group(1)
  return Redirect(RTMPVideoItem(LLNW_ROOT, clip))

