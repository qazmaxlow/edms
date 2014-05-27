from models import Source

def init_test_source():
	sources = []
	sources.append(Source(name='Other Areas (Block D & Canteen)', xml_url='en-trak1040.d.en-trak.com'))
	sources.append(Source(name='Lights, Plugs, and Centres', xml_url='egauge2199.egaug.es'))
	sources.append(Source(name='Aesthetic & Wisdom Blocks', xml_url='en-trak1040.d.en-trak.com'))
	sources.append(Source(name='New LP', xml_url='egauge2199.egaug.es'))
	sources.append(Source(name='Hall-Canteen-Special Room Block', xml_url='en-trak1040.d.en-trak.com'))
	sources.append(Source(name='Block A', xml_url='en-trak1040.d.en-trak.com'))
	sources.append(Source(name='Essential Lights & Power', xml_url='en-trak1041.d.en-trak.com'))

	Source.objects.insert(sources)
