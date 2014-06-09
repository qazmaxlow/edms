from egauge.models import Source
from system.models import System

def init_test_source():
	sources = []
	sources.append(Source(name='Aircon Total', xml_url='egauge4459.egaug.es', system_code='nike', system_path=None))
	sources.append(Source(name='Showroom Sockets', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk', system_path=',adidas,'))
	sources.append(Source(name='Lights Plugs Total', xml_url='egauge4459.egaug.es', system_code='nike', system_path=None))
	sources.append(Source(name='showroom Lights', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk', system_path=',adidas,'))
	sources.append(Source(name='Aircon Main', xml_url='egauge4459.egaug.es', system_code='nike', system_path=None))
	sources.append(Source(name='Aircon Hall', xml_url='egauge4459.egaug.es', system_code='nike', system_path=None))
	sources.append(Source(name='Air Conditioning', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw', system_path=',adidas,'))
	sources.append(Source(name='Lights & Plugs', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw', system_path=',adidas,'))
	sources.append(Source(name='Lights & Plugs', xml_url='egauge984.egaug.es', system_code='adidas-shatin', system_path=',adidas,adidas-hk'))
	sources.append(Source(name='Blocks AB', xml_url='en-trak1010.d.en-trak.com', system_code='adidas', system_path=None))

	Source.objects.insert(sources)

def init_test_system():
	systems = []
	systems.append(System(code='adidas', path=None, name='Adidas'))
	systems.append(System(code='adidas-hk', path=',adidas,', name='Adidas Hong Kong'))
	systems.append(System(code='adidas-tw', path=',adidas,', name='Adidas Taiwan'))
	systems.append(System(code='nike', path=None, name='Nike'))
	systems.append(System(code='adidas-shatin', path=',adidas,adidas-hk,', name='Adidas Shatin'))

	System.objects.insert(systems)
