import collections
import os

import requests
import requests_cache
from lxml import html, etree
import yaml

#requests_cache.install_cache(allowable_codes=(200,301,404))
_parser = html.HTMLParser(encoding="utf-8")

def parseTime(time):
  def _parseTime(t):
    n, _, suf = t.partition(" ")
    return int(n) + (12 if suf.lower() == "pm" else 0)
  s, _, e = time.partition(" - ")
  s, e = _parseTime(s), _parseTime(e)
  e = e + 24 if e < s else e
  return [v % 24 for v in range(s,e)], "{:d}{} to {:d}{}".format(s%12, "am" if s%24 <= 12 else "pm", e%12, "am" if e%24 <= 12 else "pm")

def dlimg(fname, url):
  if os.path.exists(fname):
        return fname
  if url:
    r = requests.get(url)
    if r.status_code == 200:
      with open(fname, 'wb') as f:
        f.write(r.content)
        return fname
  return False

def main():
  def makeData():
    return {
      "time": {},
      "price": {},
      "months": {},
    }
  data = collections.defaultdict(makeData)

  def add(typ, hemi, elems):
    o = 1 if typ == "fish" else 0
    for el in elems[1:]:
      name = el[0][0].text.strip()
      imgs = el[1].xpath('.//a/@href')
      imageURL = imgs[0] if len(imgs) > 0 else ""
      price = el[2].text.strip().replace(",","")
      time = el[4+o][0].text.strip() if len(el[4+o]) > 0 else el[3+o][0][0].text.strip() # Diving beetle hack
      months = []
      for (i, mEl) in enumerate(el[5+o:]):
        if "✓" in mEl.text:
          months.append(i+1)
      price = 0 if price == "?" or price == "-" else int(price)
      times, time = (list(range(24)), "All Day") if time.lower() == "all day" or time == "?" else parseTime(time)
      _id = name.lower().replace(" ", "")
      data[_id]["type"] = typ
      data[_id]["name"] = name
      data[_id]["time"] = time.replace("-", "to")
      data[_id]["times"] = times
      data[_id]["price"][hemi] = price
      data[_id]["months"][hemi] = months
      data[_id]["image"] = dlimg('images/icons/{}.png'.format(_id), imageURL)

  def addShell(name, price, url=""):
    _id = name.lower().replace(" ", "")
    data[_id] = {
      "type": "shell",
      "name": name,
      "time":"All Day",
      "times": list(range(24)),
      "months": {
        "north": [1,2,3,4,5,6,7,8,9,10,11,12],
        "south": [1,2,3,4,5,6,7,8,9,10,11,12],
      },
      "price": {
        "north": price,
        "south": price,
      },
      "image": dlimg('images/icons/{}.png'.format(_id), url)
    }

  r = requests.get("https://animalcrossing.fandom.com/wiki/Fish_(New_Horizons)")
  if r.status_code != 200:
    print(r)
    return
  doc = html.fromstring(r.content, parser=_parser)
  add("fish", "north", doc.xpath('//*[@title="Northern Hemisphere"]//table[@class="roundy sortable"]//tr'))
  add("fish", "south", doc.xpath('//*[@title="Southern Hemisphere"]//table[@class="roundy sortable"]//tr'))

  r = requests.get("https://animalcrossing.fandom.com/wiki/Bugs_(New_Horizons)")
  if r.status_code != 200:
    print(r)
    return
  doc = html.fromstring(r.content, parser=_parser)
  add("bug", "north", doc.xpath('//*[@title="Northern Hemisphere"]//table[@class="sortable"]//tr'))
  add("bug", "south", doc.xpath('//*[@title="Southern Hemisphere"]//table[@class="sortable"]//tr'))

  # Manually add shells
  addShell("Conch", 700)
  addShell("Coral", 250)
  addShell("Cowries", 60)
  addShell("Giant clam", 450)
  addShell("Oyster shell", 450)
  addShell("Pearl oyster", 1200)
  addShell("Porceletta", 30)
  addShell("Sand dollar", 120)
  addShell("Sea snail", 180)
  addShell("Scallop shell", 600)
  addShell("Venus comb", 150)
  addShell("White scallop", 450)

  with open('_data/items.yml', 'w') as f:
    yaml.dump(sorted(data.values(), key=lambda i: i["name"]), f, default_flow_style=None)

main()
