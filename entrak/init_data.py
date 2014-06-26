# -*- coding: utf-8 -*-
import datetime
from egauge.models import Source
from system.models import System
from unit.models import Unit

def init_test_source():
	sources = []
	sources.append(Source(
		name='Aircon Total', xml_url='egauge4459.egaug.es', system_code='nike',
		system_path=None, d_name='Aircon Total', d_name_tc=u'總冷氣', order=2,
		units={'co2': 1 ,'charge': 1}))
	sources.append(Source(
		name='Showroom Sockets', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk',
		system_path=',adidas,', d_name='Showroom Sockets', d_name_tc=u'電制', order=1,
		units={'co2': 1, 'charge': 1}))
	sources.append(Source(name='Lights Plugs Total', xml_url='egauge4459.egaug.es',system_code='nike',
		system_path=None, d_name='Lights Plugs Total', d_name_tc=u'燈及電制', order=1,
		units={'co2': 1, 'charge': 1}))
	sources.append(Source(
		name='showroom Lights', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk',
		system_path=',adidas,', d_name='showroom Lights', d_name_tc=u'燈', order=2,
		units={'co2': 1, 'charge': 1}))
	sources.append(Source(name='Aircon Main', xml_url='egauge4459.egaug.es', system_code='nike',
		system_path=None, d_name='Aircon Main', d_name_tc=u'主冷氣', order=4,
		units={'co2': 1, 'charge': 1}))
	sources.append(Source(name='Aircon Hall', xml_url='egauge4459.egaug.es', system_code='nike',
		system_path=None, d_name='Aircon Hall', d_name_tc=u'禮堂空調', order=3,
		units={'co2': 1, 'charge': 1}))
	sources.append(Source(name='Air Conditioning', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw',
		system_path=',adidas,', d_name='Air Conditioning', d_name_tc=u'空調', order=2,
		units={'co2': 2, 'charge': 3}))
	sources.append(Source(name='Lights & Plugs', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw',
		system_path=',adidas,', d_name='Lights & Plugs', d_name_tc=u'燈及電制', order=1,
		units={'co2': 2, 'charge': 3}))
	sources.append(Source(name='Lights & Plugs', xml_url='egauge984.egaug.es', system_code='adidas-shatin',
		system_path=',adidas,adidas-hk', d_name='Lights & Plugs', d_name_tc=u'燈及電制', order=1,
		units={'co2': 2, 'charge': 1}))
	sources.append(Source(name='Blocks AB', xml_url='en-trak1010.d.en-trak.com', system_code='adidas',
		system_path=None, d_name='Blocks AB', d_name_tc=u'AB大樓', order=1,
		units={'co2': 1, 'charge': 2}))

	Source.objects.insert(sources)

def init_test_system():
	systems = []
	systems.append(System(code='adidas', path='', name='Adidas'))
	systems.append(System(code='adidas-hk', path=',adidas,', name='Adidas Hong Kong'))
	systems.append(System(code='adidas-tw', path=',adidas,', name='Adidas Taiwan'))
	systems.append(System(code='nike', path='', name='Nike'))
	systems.append(System(code='adidas-shatin', path=',adidas,adidas-hk,', name='Adidas Shatin'))

	System.objects.bulk_create(systems)

def init_test_unit():
	units = []
	units.append(Unit(category='co2', cat_name='kg CO2', cat_id=1,
		name='NT co2', rate=0.5, effective_date=datetime.datetime(2014, 4, 30, 16), order=2))
	units.append(Unit(category='co2', cat_name='kg CO2', cat_id=1,
		name='NT co2', rate=0.75, effective_date=datetime.datetime(2014, 6, 3, 16), order=2))
	units.append(Unit(category='co2', cat_name='kg CO2', cat_id=2,
		name='KL co2', rate=0.25, effective_date=datetime.datetime(2014, 4, 30, 16), order=2))
	units.append(Unit(category='charge', cat_name='$', cat_id=1,
		name=u'clp', rate=1.5, effective_date=datetime.datetime(2014, 4, 30, 16), order=1))
	units.append(Unit(category='charge', cat_name='$', cat_id=2,
		name=u'hkec', rate=4.5, effective_date=datetime.datetime(2014, 4, 30, 16), order=1))
	units.append(Unit(category='charge', cat_name='$', cat_id=3,
		name=u'twec', rate=0.8, effective_date=datetime.datetime(2014, 4, 30, 16), order=1))

	Unit.objects.insert(units)
