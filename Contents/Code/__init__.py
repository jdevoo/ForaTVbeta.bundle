from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
import urllib

FTV_PREFIX = '/video/foratvbeta1'
FTV_ROOT   = 'http://fora.tv'
FTV_TOPICS = ['Economy', 'Environment', 'Politics', 'Science', 'Technology', 'Culture']
CACHE_INTERVAL	= 3600 * 6

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
  dir.Append(Function(DirectoryItem(MostStarMenu, title="Week's Most Watched"), choice='views'))
  dir.Append(Function(DirectoryItem(MostStarMenu, title="Week's Most Commented"), choice='comments'))
  dir.Append(Function(DirectoryItem(TopicMenu, title="By Topic")))
  dir.Append(Function(SearchDirectoryItem(SearchMenu, thumb=R('icon-default.png'), title='Search FORA.tv', prompt='Search FORA.tv')))
  return dir

def FeaturedMenu(sender, choice=''):
  dir = MediaContainer(viewGroup='InfoList', title2='Featured' if choice == '' else choice)
  for e in XML.ElementFromURL(FTV_ROOT if choice == '' else FTV_ROOT+'/topic/'+choice, True).xpath('//div[@class="featured_bit"]'):
    title = e.xpath('.//div[@class="featured_title"]/a')[0].text
    key = e.xpath('.//a')[0].get('href')+'#full_program'
    thumb = e.xpath('.//a/img')[0].get('src')
    subtitle = e.xpath('.//div[@class="l_partner"]/a')[0].text
    dir.Append(WebVideoItem(FTV_ROOT+key, title, subtitle, thumb=FTV_ROOT+thumb))
  return dir

def TopicMenu(sender, choice=''):
  dir = MediaContainer(viewGroup='List', title2=choice.split('/')[0].title())
  if choice == '':
    for topic in FTV_TOPICS:
      dir.Append(Function(DirectoryItem(TopicMenu, title=topic), choice=topic))
  elif choice in FTV_TOPICS:
    dir.Append(Function(DirectoryItem(FeaturedMenu, title="Featured"), choice=choice))
    dir.Append(Function(DirectoryItem(TopicMenu, title="Most Recent"), choice=choice.lower()+'/all'))
  else:
    dir.viewGroup = 'InfoList'
    for e in XML.ElementFromURL(FTV_ROOT+'/topic/'+choice, True).xpath('//div[@class="featured_bit"]'):
      title = e.xpath('.//div[@class="featured_title"]/a')[0].text
      key = e.xpath('.//div[@class="featured_title"]/a')[0].get('href')+'#full_program'
      thumb = e.xpath('.//div[@class="cropped_image"]')[0].get('style')
      subtitle = e.xpath('.//div[@class="l_partner"]/a')[0].text
      summary = 'Views: %s\nComments: %s' % (e.xpath('.//span[@class="views"]')[0].text, e.xpath('.//span[@class="views"]')[1].text)
      dir.Append(WebVideoItem(FTV_ROOT+key, title, subtitle, summary, thumb=FTV_ROOT+thumb[thumb.find('(')+1:thumb.find(')')]))
  return dir

def MostStarMenu(sender, choice):
  dir = MediaContainer(viewGroup='InfoList', title2="Week's Most Watched" if choice == 'views' else "Week's Most Commented")
  res = []
  for topic in map(str.lower, FTV_TOPICS):
    for e in XML.ElementFromURL('%s/topic/%s/all?sort=%s' % (FTV_ROOT, topic, choice), True).xpath('//div[@class="featured_bit"]'):
      title = e.xpath('.//div[@class="featured_title"]/a')[0].text
      key = e.xpath('.//div[@class="featured_title"]/a')[0].get('href')+'#full_program'
      thumb = e.xpath('.//div[@class="cropped_image"]')[0].get('style')
      subtitle = e.xpath('.//div[@class="l_partner"]/a')[0].text
      c = int(e.xpath('.//span[@class="views"]')[0 if choice == 'views' else 1].text.replace(',', ''))
      res += [(c, key, title, subtitle, thumb, topic)]
  sres = sorted(res, key=lambda item: item[0])
  for item in sres[0:10]:
    dir.Append(WebVideoItem(FTV_ROOT+item[1], item[2], item[3], item[5].title()+'\n'+str(item[0])+(' Views' if choice == 'views' else ' Comments'), thumb=FTV_ROOT+item[4][item[4].find('(')+1:item[4].find(')')]))
  return dir

def SearchMenu(sender, query):
  dir = MediaContainer(viewGroup='InfoList', title2=query)
  for e in XML.ElementFromURL(FTV_ROOT+'/search_video?%s&per_page=50' % urllib.urlencode({'q':query}), True).xpath('//div[@class="clip_bit "]'):
    title = e.xpath('.//a[@class="clip_bit_title"]')[0].text
    key = e.xpath('.//a[@class="cropped_thumb"]')[0].get('href')+'#full_program'
    thumb = e.xpath('.//a[@class="cropped_thumb"]/img')[0].get('src')
    subtitle = e.xpath('.//div[@class="l_partner"]/a')[0].text
    summary = 'Views: %s\nComments: %s' % (e.xpath('.//span[@class="views"]')[0].text, e.xpath('.//span[@class="views"]')[1].text)
    dir.Append(WebVideoItem(FTV_ROOT+key, title, subtitle, summary, thumb=FTV_ROOT+thumb))
  return dir

