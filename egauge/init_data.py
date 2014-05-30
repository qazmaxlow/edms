from models import Source

def init_test_source():
	sources = []
	sources.append(Source(name='Aircon Total', xml_url='egauge4459.egaug.es'))
	sources.append(Source(name='Showroom Sockets', xml_url='en-trak1039.d.en-trak.com'))
	sources.append(Source(name='Lights Plugs Total', xml_url='egauge4459.egaug.es'))
	sources.append(Source(name='showroom Lights', xml_url='en-trak1039.d.en-trak.com'))
	sources.append(Source(name='Aircon Main', xml_url='egauge4459.egaug.es'))
	sources.append(Source(name='Aircon Hall', xml_url='egauge4459.egaug.es'))
	sources.append(Source(name='Air Conditioning', xml_url='en-trak1012.d.en-trak.com'))

	Source.objects.insert(sources)
