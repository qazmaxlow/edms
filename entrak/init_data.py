# -*- coding: utf-8 -*-
import datetime
import json
import pytz
from egauge.models import Source
from system.models import System, BaselineUsage, UnitCategory, Unit, UnitRate

def init_test_source():
	sources = []
	sources.append(Source(
		name='Aircon Total', xml_url='egauge4459.egaug.es', system_code='nike',
		system_path=None, d_name='Aircon Total', d_name_tc=u'總冷氣', order=2,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	sources.append(Source(
		name='Showroom Sockets', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk',
		system_path=',adidas,', d_name='Showroom Sockets', d_name_tc=u'電制', order=1,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 11, 15))))
	sources.append(Source(name='Lights Plugs Total', xml_url='egauge4459.egaug.es',system_code='nike',
		system_path=None, d_name='Lights Plugs Total', d_name_tc=u'燈及電制', order=1,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	sources.append(Source(
		name='showroom Lights', xml_url='en-trak1039.d.en-trak.com', system_code='adidas-hk',
		system_path=',adidas,', d_name='showroom Lights', d_name_tc=u'燈', order=2,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 1))))
	sources.append(Source(name='Aircon Main', xml_url='egauge4459.egaug.es', system_code='nike',
		system_path=None, d_name='Aircon Main', d_name_tc=u'主冷氣', order=4,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	sources.append(Source(name='Aircon Hall', xml_url='egauge4459.egaug.es', system_code='nike',
		system_path=None, d_name='Aircon Hall', d_name_tc=u'禮堂空調', order=3,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	sources.append(Source(name='Air Conditioning', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw',
		system_path=',adidas,', d_name='Air Conditioning', d_name_tc=u'空調', order=2,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	sources.append(Source(name='Lights & Plugs', xml_url='en-trak1012.d.en-trak.com', system_code='adidas-tw',
		system_path=',adidas,', d_name='Lights & Plugs', d_name_tc=u'燈及電制', order=1,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	sources.append(Source(name='Lights & Plugs', xml_url='egauge984.egaug.es', system_code='adidas-shatin',
		system_path=',adidas,adidas-hk', d_name='Lights & Plugs', d_name_tc=u'燈及電制', order=1,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))
	sources.append(Source(name='Blocks AB', xml_url='en-trak1010.d.en-trak.com', system_code='adidas',
		system_path=None, d_name='Blocks AB', d_name_tc=u'AB大樓', order=1,
		first_record=pytz.timezone("Asia/Hong_Kong").localize(datetime.datetime(2013, 10, 15))))

	Source.objects.insert(sources)

def init_test_system():
	systems = []
	systems.append(System(code='adidas', path='', name='Adidas', unit_info=json.dumps({'1': 'hk-co2' ,'2': 'clp'})))
	systems.append(System(code='adidas-hk', path=',adidas,', name='Adidas Hong Kong', unit_info=json.dumps({'1': 'hk-co2' ,'2': 'clp'})))
	systems.append(System(code='adidas-tw', path=',adidas,', name='Adidas Taiwan', unit_info=json.dumps({'1': 'tw-co2', '2': 'twec'})))
	systems.append(System(code='nike', path='', name='Nike', unit_info=json.dumps({'1': 'hk-co2' ,'2': 'clp'})))
	systems.append(System(code='adidas-shatin', path=',adidas,adidas-hk,', name='Adidas Shatin',
		unit_info=json.dumps({'1': 'tw-co2', '2': 'clp'})))

	System.objects.bulk_create(systems)

def init_test_unit():
	unit_cats = []
	unit_cats.append(UnitCategory(name='co2', order=1, img_off='co2.png', img_on='co2-hover.png', bg_img='burger-bg.png'))
	unit_cats.append(UnitCategory(name='currency', order=2, img_off='money.png', img_on='money-hover.png', bg_img='burger-bg.png'))
	UnitCategory.objects.bulk_create(unit_cats)

	units = []
	units.append(Unit(category_id=1, code='hk-co2'))
	units.append(Unit(category_id=1, code='tw-co2'))
	units.append(Unit(category_id=2, code=u'clp'))
	units.append(Unit(category_id=2, code=u'hkec'))
	units.append(Unit(category_id=2, code=u'twec'))
	Unit.objects.bulk_create(units)

	unit_rates = []
	unit_rates.append(UnitRate(unit_id=1, rate=0.5, effective_date=datetime.datetime(2014, 4, 30, 16)))
	unit_rates.append(UnitRate(unit_id=1, rate=0.75, effective_date=datetime.datetime(2014, 6, 3, 16)))
	unit_rates.append(UnitRate(unit_id=2, rate=0.25, effective_date=datetime.datetime(2014, 4, 30, 16)))
	unit_rates.append(UnitRate(unit_id=3, rate=1.5, effective_date=datetime.datetime(2014, 4, 30, 16)))
	unit_rates.append(UnitRate(unit_id=4, rate=4.5, effective_date=datetime.datetime(2014, 4, 30, 16)))
	unit_rates.append(UnitRate(unit_id=5, rate=0.8, effective_date=datetime.datetime(2014, 4, 30, 16)))
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
