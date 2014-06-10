# -*- coding: utf-8 -*-
from egauge.models import Source
from system.models import System

def init_test_source():
	sources = []
	sources.append(Source(name='Aircon Total', xml_url='egauge4459.egaug.es', system_code='nike', system_path=None, d_name='Aircon Total', d_name_tc=u'總冷氣', order=2))
	sources.append(Source(name='Showroom Sockets', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk', system_path=',adidas,', d_name='Showroom Sockets', d_name_tc=u'電制', order=1))
	sources.append(Source(name='Lights Plugs Total', xml_url='egauge4459.egaug.es', system_code='nike', system_path=None, d_name='Lights Plugs Total', d_name_tc=u'燈及電制', order=1))
	sources.append(Source(name='showroom Lights', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk', system_path=',adidas,', d_name='showroom Lights', d_name_tc=u'燈', order=2))
	sources.append(Source(name='Aircon Main', xml_url='egauge4459.egaug.es', system_code='nike', system_path=None, d_name='Aircon Main', d_name_tc=u'主冷氣', order=4))
	sources.append(Source(name='Aircon Hall', xml_url='egauge4459.egaug.es', system_code='nike', system_path=None, d_name='Aircon Hall', d_name_tc=u'禮堂空調', order=3))
	sources.append(Source(name='Air Conditioning', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw', system_path=',adidas,', d_name='Air Conditioning', d_name_tc=u'空調', order=2))
	sources.append(Source(name='Lights & Plugs', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw', system_path=',adidas,', d_name='Lights & Plugs', d_name_tc=u'燈及電制', order=1))
	sources.append(Source(name='Lights & Plugs', xml_url='egauge984.egaug.es', system_code='adidas-shatin', system_path=',adidas,adidas-hk', d_name='Lights & Plugs', d_name_tc=u'燈及電制', order=1))
	sources.append(Source(name='Blocks AB', xml_url='en-trak1010.d.en-trak.com', system_code='adidas', system_path=None, d_name='Blocks AB', d_name_tc=u'AB大樓', order=1))

	Source.objects.insert(sources)

def init_test_system():
	systems = []
	systems.append(System(code='adidas', path=None, name='Adidas'))
	systems.append(System(code='adidas-hk', path=',adidas,', name='Adidas Hong Kong'))
	systems.append(System(code='adidas-tw', path=',adidas,', name='Adidas Taiwan'))
	systems.append(System(code='nike', path=None, name='Nike'))
	systems.append(System(code='adidas-shatin', path=',adidas,adidas-hk,', name='Adidas Shatin'))

	System.objects.insert(systems)
