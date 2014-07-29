# -*- coding: utf-8 -*-
import datetime
import json
import pytz
from egauge.models import Source
from system.models import System
from unit.models import UnitCategory, UnitRate
from baseline.models import BaselineUsage

def init_test_source():
	sources = []
	sources.append(Source(
		name='Aircon Total', xml_url='egauge4459.egaug.es', system_code='nike',
		system_path=None, d_name='Aircon Total', d_name_tc=u'總冷氣', order=2))
	sources.append(Source(
		name='Showroom Sockets', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk',
		system_path=',adidas,', d_name='Showroom Sockets', d_name_tc=u'電制', order=1))
	sources.append(Source(name='Lights Plugs Total', xml_url='egauge4459.egaug.es',system_code='nike',
		system_path=None, d_name='Lights Plugs Total', d_name_tc=u'燈及電制', order=1))
	sources.append(Source(
		name='showroom Lights', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk',
		system_path=',adidas,', d_name='showroom Lights', d_name_tc=u'燈', order=2))
	sources.append(Source(name='Aircon Main', xml_url='egauge4459.egaug.es', system_code='nike',
		system_path=None, d_name='Aircon Main', d_name_tc=u'主冷氣', order=4))
	sources.append(Source(name='Aircon Hall', xml_url='egauge4459.egaug.es', system_code='nike',
		system_path=None, d_name='Aircon Hall', d_name_tc=u'禮堂空調', order=3))
	sources.append(Source(name='Air Conditioning', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw',
		system_path=',adidas,', d_name='Air Conditioning', d_name_tc=u'空調', order=2))
	sources.append(Source(name='Lights & Plugs', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw',
		system_path=',adidas,', d_name='Lights & Plugs', d_name_tc=u'燈及電制', order=1))
	sources.append(Source(name='Lights & Plugs', xml_url='egauge984.egaug.es', system_code='adidas-shatin',
		system_path=',adidas,adidas-hk,', d_name='Lights & Plugs', d_name_tc=u'燈及電制', order=1))
	sources.append(Source(name='Blocks AB', xml_url='en-trak1010.d.en-trak.com', system_code='adidas',
		system_path=None, d_name='Blocks AB', d_name_tc=u'AB大樓', order=1))

	Source.objects.insert(sources)

def init_test_system():
	systems = []
	systems.append(System(code='adidas', path='', name='Adidas', unit_info=json.dumps({'co2': 'hk-co2' ,'money': 'clp'}),
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	systems.append(System(code='adidas-hk', path=',adidas,', name='Adidas Hong Kong',
		unit_info=json.dumps({'co2': 'hk-co2' ,'money': 'clp'}),
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	systems.append(System(code='adidas-tw', path=',adidas,', name='Adidas Singapore',
		unit_info=json.dumps({'co2': 'tw-co2', 'money': 'twec'}),
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	systems.append(System(code='nike', path='', name='Nike', unit_info=json.dumps({'co2': 'hk-co2' ,'money': 'clp'}),
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	systems.append(System(code='adidas-shatin', path=',adidas,adidas-hk,', name='Adidas Shatin',
		unit_info=json.dumps({'co2': 'tw-co2', 'money': 'clp'}),
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))

	System.objects.bulk_create(systems)

def init_unit_category():
	unit_cats = []
	unit_cats.append(UnitCategory(code='kwh', name='kWh', order=0,
		short_desc='kWh', img_off='kwh.png', img_on='kwh-hover.png', bg_img='burger-bg.png',
		city='all'))
	unit_cats.append(UnitCategory(code='money', name='HK$', short_desc='HK$', order=1,
		img_off='money.png', img_on='money-hover.png', bg_img='burger-bg.png', city='hk',
		has_detail_rate=True, is_suffix=False))
	unit_cats.append(UnitCategory(code='money', name='SG$', short_desc='SG$', order=1,
		img_off='money.png', img_on='money-hover.png', bg_img='burger-bg.png', city='sg',
		has_detail_rate=True, is_suffix=False))
	unit_cats.append(UnitCategory(code='co2', name='kg CO2', short_desc='kg CO2', order=2,
		img_off='co2.png', img_on='co2-hover.png', bg_img='burger-bg.png', city='all',
		has_detail_rate=True))
	unit_cats.append(UnitCategory(code='burger', name='bugers', short_desc='bugers', order=3,
		img_off='burger.png', img_on='burger-hover.png', bg_img='burger-bg.png', city='all',
		global_rate=2.15))
	unit_cats.append(UnitCategory(code='noodle', name='bowls of noodle',
		short_desc='bowls of noodle', order=4, img_off='ramen.png', img_on='ramen-hover.png',
		bg_img='burger-bg.png', city='all', global_rate=0.52))
	unit_cats.append(UnitCategory(code='pineapplebuns', name='pineapple buns', short_desc='pineapple buns', order=5,
		img_off='bun.png', img_on='bun-hover.png', bg_img='burger-bg.png', city='all', global_rate=3.3))
	unit_cats.append(UnitCategory(code='icecream', name='ice cream cones', short_desc='ice cream cones', order=6,
		img_off='icecream.png', img_on='icecream-hover.png', bg_img='burger-bg.png', city='all', global_rate=0.2))
	unit_cats.append(UnitCategory(code='taxitrip', name='taxi trips btwn HK Airport and Times Square',
		short_desc='taxi trips', order=7, img_off='taxi.png', img_on='taxi-hover.png',
		bg_img='burger-bg.png', city='hk', global_rate=0.0325))
	unit_cats.append(UnitCategory(code='taxitrip', name='taxi trips btwn Changi Airport and Marina Bay Sands',
		short_desc='taxi trips', order=7, img_off='taxi.png', img_on='taxi-hover.png',
		bg_img='burger-bg.png', city='sg', global_rate=0.065))
	unit_cats.append(UnitCategory(code='biketrip', name='bike trips btwn HK Airport and Times Square',
		short_desc='bike trips', order=8, img_off='bike.png', img_on='bike-hover.png',
		bg_img='burger-bg.png', city='hk', global_rate=1.87))
	unit_cats.append(UnitCategory(code='biketrip', name='bike trips btwn Changi Airport and Marina Bay Sands',
		short_desc='bike trips', order=8, img_off='bike.png', img_on='bike-hover.png',
		bg_img='burger-bg.png', city='sg', global_rate=3.74))
	unit_cats.append(UnitCategory(code='walkingtrip', name='walking trips btwn HK Airport and Times Square',
		short_desc='walking trips', order=9, img_off='walking.png', img_on='walking-hover.png',
		bg_img='burger-bg.png', city='hk', global_rate=0.357))
	unit_cats.append(UnitCategory(code='walkingtrip', name='walking trips btwn Changi Airport and Marina Bay Sands',
		short_desc='walking trips', order=9, img_off='walking.png', img_on='walking-hover.png',
		bg_img='burger-bg.png', city='sg', global_rate=0.714))
	UnitCategory.objects.bulk_create(unit_cats)

def init_test_unit_rates():
	unit_rates = []
	unit_rates.append(UnitRate(category_code='co2', code='hk-co2', rate=0.5, effective_date=datetime.datetime(2014, 4, 30, 16)))
	unit_rates.append(UnitRate(category_code='co2', code='hk-co2', rate=0.75, effective_date=datetime.datetime(2014, 6, 3, 16)))
	unit_rates.append(UnitRate(category_code='co2', code='sg-co2', rate=0.25, effective_date=datetime.datetime(2014, 4, 30, 16)))
	unit_rates.append(UnitRate(category_code='money', code=u'clp', rate=1.5, effective_date=datetime.datetime(2014, 4, 30, 16)))
	unit_rates.append(UnitRate(category_code='money', code=u'hkec', rate=4.5, effective_date=datetime.datetime(2014, 4, 30, 16)))
	unit_rates.append(UnitRate(category_code='money', code=u'sgec', rate=0.8, effective_date=datetime.datetime(2014, 4, 30, 16)))
	UnitRate.objects.bulk_create(unit_rates)

def init_test_baseline_usage():
	baseline_usages = []

	hk_tz = pytz.timezone("Asia/Hong_Kong")

	for i in [1, 2, 3, 5]:
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 3, 2)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 3, 27)), usage=1000))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 3, 28)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 4, 28)), usage=1200))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 4, 29)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 5, 29)), usage=1300))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 5, 30)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 6, 30)), usage=900))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 7, 1)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 7, 31)), usage=800))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 8, 1)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 9, 2)), usage=1000))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 9, 3)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 9, 29)), usage=1000))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 9, 30)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 11, 2)), usage=1200))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 11, 3)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 11, 29)), usage=1200))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 11, 30)),
			end_dt=hk_tz.localize(datetime.datetime(2012, 12, 1)), usage=1300))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2012, 12, 2)),
			end_dt=hk_tz.localize(datetime.datetime(2013, 1, 3)), usage=1000))
		baseline_usages.append(BaselineUsage(system_id=i, start_dt=hk_tz.localize(datetime.datetime(2013, 1, 4)),
			end_dt=hk_tz.localize(datetime.datetime(2013, 2, 5)), usage=950))

	BaselineUsage.objects.bulk_create(baseline_usages)
