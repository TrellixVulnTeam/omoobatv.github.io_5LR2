# -*- coding: utf-8 -*-
from modules import kodi_utils
from modules.settings_reader import get_setting, set_setting
# logger = kodi_utils.logger

ls = kodi_utils.local_string

def build_navigate_to_page(params):
	import json
	from modules.settings import nav_jump_use_alphabet
	use_alphabet = nav_jump_use_alphabet()
	icon = kodi_utils.translate_path('special://home/addons/script.tikiart/resources/media/item_jump.png')
	fanart = kodi_utils.translate_path('special://home/addons/plugin.video.fen/fanart.png')
	media_type = params.get('media_type')
	def _builder(use_alphabet):
		for i in start_list:
			if use_alphabet: line1, line2 = i.upper(), ls(32821) % (media_type, i.upper())
			else: line1, line2 = '%s %s' % (ls(32022), i), ls(32822) % i
			yield {'line1': line1, 'line2': line2, 'icon': icon}
	if use_alphabet:
		start_list = [chr(i) for i in range(97,123)]
	else:
		start_list = [str(i) for i in range(1, int(params.get('total_pages'))+1)]
		start_list.remove(params.get('current_page'))
	list_items = list(_builder(use_alphabet))
	kwargs = {'items': json.dumps(list_items), 'heading': 'Fen', 'enumerate': 'false', 'multi_choice': 'false', 'multi_line': 'false'}
	new_start = kodi_utils.select_dialog(start_list, **kwargs)
	kodi_utils.sleep(100)
	if new_start == None: return
	if use_alphabet: new_page, new_letter = '', new_start
	else: new_page, new_letter = new_start, None
	url_params = {'mode': params.get('transfer_mode', ''), 'action': params.get('transfer_action', ''), 'new_page': new_page, 'new_letter': new_letter,
				'media_type': params.get('media_type', ''), 'query': params.get('query', ''), 'actor_id': params.get('actor_id', ''),
				'user': params.get('user', ''), 'slug': params.get('slug', '')}
	kodi_utils.execute_builtin('Container.Update(%s)' % kodi_utils.build_url(url_params))

def paginate_list(item_list, page, letter, limit=20):
	from modules.utils import chunks
	def _get_start_index(letter):
		if letter == 't':
			try:
				beginswith_tuple = ('s', 'the s', 'a s', 'an s')
				indexes = [i for i,v in enumerate(title_list) if v.startswith(beginswith_tuple)]
				start_index = indexes[-1:][0] + 1
			except: start_index = None
		else:
			beginswith_tuple = (letter, 'the %s' % letter, 'a %s' % letter, 'an %s' % letter)
			try: start_index = next(i for i,v in enumerate(title_list) if v.startswith(beginswith_tuple))
			except: start_index = None
		return start_index
	if letter != 'None':
		from itertools import chain, zip_longest
		title_list = [i['title'].lower() for i in item_list]
		start_list = [chr(i) for i in range(97,123)]
		letter_index = start_list.index(letter)
		base_list = [element for element in list(chain.from_iterable([val for val in zip_longest(start_list[letter_index:], start_list[:letter_index][::-1])])) if element != None]
		for i in base_list:
			start_index = _get_start_index(i)
			if start_index: break
		item_list = item_list[start_index:]
	pages = list(chunks(item_list, limit))
	total_pages = len(pages)
	return pages[page - 1], total_pages

def toggle_jump_to():
	from modules.settings import nav_jump_use_alphabet
	(setting, new_action) = ('0', ls(32022)) if nav_jump_use_alphabet() else ('1', ls(32023))
	set_setting('nav_jump', setting)
	kodi_utils.execute_builtin('Container.Refresh')
	kodi_utils.notification(ls(32851) % new_action)

def open_settings(query, addon='plugin.video.fen'):
	kodi_utils.sleep(250)
	if query:
		try:
			button, control = 100, 80
			kodi_utils.hide_busy_dialog()
			menu, function = query.split('.')
			kodi_utils.execute_builtin('Addon.OpenSettings(%s)' % addon)
			kodi_utils.execute_builtin('SetFocus(%i)' % (int(menu) - button))
			kodi_utils.execute_builtin('SetFocus(%i)' % (int(function) - control))
		except: kodi_utils.execute_builtin('Addon.OpenSettings(%s)' % addon)
	else: kodi_utils.execute_builtin('Addon.OpenSettings(%s)' % addon)

def clean_settings():
	import xml.etree.ElementTree as ET
	def _make_content(dict_object):
		content = '<settings version="2">'
		for item in dict_object:
			_id = item['id']
			if _id in active_settings:
				if 'default' in item and 'value' in item: content += '\n    <setting id="%s" default="%s">%s</setting>' % (_id, item['default'], item['value'])
				elif 'default' in item: content += '\n    <setting id="%s" default="%s"></setting>' % (_id, item['default'])
				elif 'value' in item: content += '\n    <setting id="%s">%s</setting>' % (_id, item['value'])
				else: content += '\n    <setting id="%s"></setting>'
			else: removed_append(item)
		content += '\n</settings>'
		return content
	kodi_utils.close_all_dialog()
	kodi_utils.sleep(200)
	kodi_utils.progressDialog.create(ls(32577), '')
	kodi_utils.progressDialog.update(0)
	addon_ids = ('plugin.video.fen', 'script.module.fenomscrapers', 'script.module.myaccounts')
	addon_settings = 'special://home/addons/%s/resources/settings.xml'
	addon_data_settings = 'special://profile/addon_data/%s/settings.xml'
	addon_names = [kodi_utils.addon(i).getAddonInfo('name') for i in addon_ids]
	addon_data_settings_xmls = [kodi_utils.translate_path(addon_data_settings % i) for i in addon_ids]
	addon_settings_xmls = [kodi_utils.translate_path(addon_settings % i) for i in addon_ids]
	params = list(zip(addon_names, addon_data_settings_xmls, addon_settings_xmls))
	for addon in params:
		try:
			if kodi_utils.progressDialog.iscanceled(): break
			current_progress = params.index(addon)+1
			removed_settings = []
			active_settings = []
			current_user_settings = []
			removed_append = removed_settings.append
			active_append = active_settings.append
			current_append = current_user_settings.append
			root = ET.parse(addon[2]).getroot()
			for item in root.findall('./category/setting'):
				setting_id = item.get('id')
				if setting_id: active_append(setting_id)
			settings_xml = addon[1]
			root = ET.parse(settings_xml).getroot()
			for item in root:
				dict_item = {}
				setting_id = item.get('id')
				setting_default = item.get('default')
				setting_value = item.text
				dict_item['id'] = setting_id
				if setting_value: dict_item['value'] = setting_value
				if setting_default: dict_item['default'] = setting_default
				current_append(dict_item)
			new_content = _make_content(current_user_settings)
			xml_file = kodi_utils.open_file(settings_xml, 'w')
			xml_file.write(new_content)
			xml_file.close()
			percent = int((current_progress/float(len(params)))*100)
			line2 = ls(32812) % addon[0]
			line3 = ls(32813) % len(removed_settings)
			kodi_utils.progressDialog.update(percent, '[CR]%s[CR]%s' % (line2, line3))
		except: kodi_utils.notification(32574, 2000)
		kodi_utils.sleep(800)
	try: kodi_utils.progressDialog.close()
	except: pass
	kodi_utils.ok_dialog(text=32576, top_space=True)

def open_MyAccounts(params):
	from myaccounts import openMASettings
	openMASettings(params.get('query', '0.0'))
	kodi_utils.sleep(100)
	while kodi_utils.get_visibility('Window.IsVisible(addonsettings)') or kodi_utils.get_property('myaccounts.active') == 'true': kodi_utils.sleep(100)
	kodi_utils.sleep(100)
	force_trakt_update = sync_MyAccounts()
	kodi_utils.sleep(100)
	open_settings(params.get('return_query', '5.0'))
	if force_trakt_update:
		from apis.trakt_api import trakt_sync_activities
		trakt_sync_activities(force_update=True)

def sync_MyAccounts(silent=False):
	import myaccounts
	from modules.settings_reader import get_setting, set_setting
	force_trakt_update = False
	all_acct = myaccounts.getAll()
	try:
		trakt_acct = all_acct.get('trakt')
		if trakt_acct.get('username') not in ('', None):
			if get_setting('trakt_user') != trakt_acct.get('username'):
				set_setting('trakt_indicators_active', 'true')
				set_setting('watched_indicators', '1')
				force_trakt_update = True
		else:
			set_setting('trakt_indicators_active', 'false')
			set_setting('watched_indicators', '0')
		set_setting('trakt_user', trakt_acct.get('username'))
		set_setting('trakt.expires', trakt_acct.get('expires'))
		set_setting('trakt.token', trakt_acct.get('token'))
	except: pass
	try:
		fu_acct = all_acct.get('furk')
		set_setting('furk_login', fu_acct.get('username'))
		set_setting('furk_password', fu_acct.get('password'))
		if fu_acct.get('api_key') != '': set_setting('furk_api_key', fu_acct.get('api_key'))
		elif get_setting('furk_api_key') != '': kodi_utils.addon('script.module.myaccounts').setSetting('furk.api.key', get_setting('furk_api_key'))
	except: pass
	try:
		en_acct = all_acct.get('easyNews')
		set_setting('easynews_user', en_acct.get('username'))
		set_setting('easynews_password', en_acct.get('password'))
	except: pass
	try:
		tmdb_acct = all_acct.get('tmdb')
		tmdb_key = tmdb_acct.get('api_key')
		if not tmdb_key: tmdb_key = '050ee5c6c85883b200be501c878a2aed'
		set_setting('tmdb_api', tmdb_key)
	except: pass
	try:
		fanart_acct = all_acct.get('fanart_tv')
		fanart_key = fanart_acct.get('api_key')
		if not fanart_key: fanart_key = 'fe073550acf157bdb8a4217f215c0882'
		set_setting('fanart_client_key', fanart_key)
	except: pass
	try:
		imdb_acct = all_acct.get('imdb')
		set_setting('imdb_user', imdb_acct.get('user'))
	except: pass
	try:
		rd_acct = all_acct.get('realdebrid')
		if get_setting('rd.username') != rd_acct.get('username'):
			set_setting('rd.username', rd_acct.get('username'))
			set_setting('rd.client_id', rd_acct.get('client_id'))
			set_setting('rd.refresh', rd_acct.get('refresh'))
			set_setting('rd.secret', rd_acct.get('secret'))
			set_setting('rd.token', rd_acct.get('token'))
			set_setting('rd.auth', rd_acct.get('token'))
	except: pass
	try:
		pm_acct = all_acct.get('premiumize')
		set_setting('pm.token', pm_acct.get('token'))
		if get_setting('pm.account_id') != pm_acct.get('username'):
			set_setting('pm.account_id', pm_acct.get('username'))
	except: pass
	try:
		ad_acct = all_acct.get('alldebrid')
		set_setting('ad.token', ad_acct.get('token'))
		if get_setting('ad.account_id') != ad_acct.get('username'):
			set_setting('ad.account_id', ad_acct.get('username'))
	except: pass
	if not silent: kodi_utils.notification(33030, time=1500)
	return force_trakt_update

def toggle_language_invoker():
	import xml.etree.ElementTree as ET
	kodi_utils.close_all_dialog()
	kodi_utils.sleep(100)
	addon_xml = kodi_utils.translate_path('special://home/addons/plugin.video.fen/addon.xml')
	current_addon_setting = get_setting('reuse_language_invoker', 'true')
	new_value = 'false' if current_addon_setting == 'true' else 'true'
	if not kodi_utils.confirm_dialog(text=ls(33018) % (current_addon_setting.upper(), new_value.upper())): return
	if new_value == 'true' and not kodi_utils.confirm_dialog(text=33019, top_space=True): return
	tree = ET.parse(addon_xml)
	root = tree.getroot()
	for item in root.iter('reuselanguageinvoker'):
		item.text = new_value
		tree.write(addon_xml)
		break
	set_setting('reuse_language_invoker', new_value)
	kodi_utils.ok_dialog(text=33020, top_space=True)
	kodi_utils.execute_builtin('LoadProfile(%s)' % kodi_utils.get_infolabel('system.profilename'))

def refresh_cached_data(meta):
	from caches.meta_cache import metacache
	try:
		media_type, tmdb_id = meta['mediatype'], meta['tmdb_id']
		metacache.delete(media_type, 'tmdb_id', tmdb_id, meta)
		if media_type == 'tvshow': metacache.delete_all_seasons_memory_cache(tmdb_id)
		kodi_utils.notification(32576)
		kodi_utils.execute_builtin('Container.Refresh')
	except: kodi_utils.notification(32574)

def clear_cache(cache_type, silent=False):
	def _confirm():
		return silent or kodi_utils.confirm_dialog()
	success = True
	if cache_type == 'meta':
		from caches.meta_cache import delete_meta_cache
		success = delete_meta_cache(silent=silent)
	elif cache_type == 'internal_scrapers':
		if not _confirm(): return
		from apis import furk_api, easynews_api
		furk_api.clear_media_results_database()
		easynews_api.clear_media_results_database()
		for item in ('pm_cloud', 'rd_cloud', 'ad_cloud', 'folders'): clear_cache(item, silent=True)
	elif cache_type == 'external_scrapers':
		from caches.providers_cache import ExternalProvidersCache
		from caches.debrid_cache import DebridCache
		data = ExternalProvidersCache().delete_cache(silent=silent)
		debrid_cache = DebridCache().clear_database()
		success = (data, debrid_cache) == ('success', 'success')
	elif cache_type == 'trakt':
		from caches.trakt_cache import clear_all_trakt_cache_data
		success = clear_all_trakt_cache_data(silent=silent)
	elif cache_type == 'imdb':
		if not _confirm(): return
		from apis.imdb_api import clear_imdb_cache
		success = clear_imdb_cache()
	elif cache_type == 'pm_cloud':
		if not _confirm(): return
		from apis.premiumize_api import PremiumizeAPI
		success = PremiumizeAPI().clear_cache()
	elif cache_type == 'rd_cloud':
		if not _confirm(): return
		from apis.real_debrid_api import RealDebridAPI
		success = RealDebridAPI().clear_cache()
	elif cache_type == 'ad_cloud':
		if not _confirm(): return
		from apis.alldebrid_api import AllDebridAPI
		success = AllDebridAPI().clear_cache()
	elif cache_type == 'folders':
		from caches.main_cache import main_cache
		main_cache.delete_all_folderscrapers()
	else: # 'list'
		if not _confirm(): return
		from caches.main_cache import main_cache
		main_cache.delete_all_lists()
	if not silent and success: kodi_utils.notification(32576)

def clear_all_cache():
	if not kodi_utils.confirm_dialog(): return
	line = '[CR]%s....[CR]%s'
	kodi_utils.progressDialog.create('Fen', '')
	caches = (('meta', '%s %s' % (ls(32527), ls(32524))), ('internal_scrapers', '%s %s' % (ls(32096), ls(32524))), ('external_scrapers', '%s %s' % (ls(32118), ls(32524))),
			('trakt', ls(32087)), ('imdb', '%s %s' % (ls(32064), ls(32524))), ('list', '%s %s' % (ls(32815), ls(32524))),
			('pm_cloud', '%s %s' % (ls(32061), ls(32524))), ('rd_cloud', '%s %s' % (ls(32054), ls(32524))), ('ad_cloud', '%s %s' % (ls(32063), ls(32524))))
	for count, cache_type in enumerate(caches, 1):
		try:
			kodi_utils.progressDialog.update(int(float(count) / float(len(caches)) * 100), line % (ls(32816), cache_type[1]))
			clear_cache(cache_type[0], silent=True)
			kodi_utils.sleep(1000)
		except: pass
	kodi_utils.progressDialog.close()
	kodi_utils.sleep(250)
	kodi_utils.ok_dialog(text=32576, top_space=True)

def refresh_artwork():
	if not kodi_utils.confirm_dialog(): return
	database = kodi_utils.database
	dbcon = database.connect(kodi_utils.translate_path('special://database/Textures13.db'), timeout=40.0, isolation_level=None)
	dbcur = dbcon.cursor()
	dbcur.execute('''PRAGMA synchronous = OFF''')
	dbcur.execute('''PRAGMA journal_mode = OFF''')
	for item in ('icon.png', 'fanart.png'):
		try:
			icon_path = kodi_utils.translate_path('special://home/addons/plugin.video.fen/%s' % item)
			dbcur.execute("SELECT cachedurl FROM texture WHERE url = ?", (icon_path,))
			image = dbcur.fetchone()[0]
			removal_path = kodi_utils.translate_path('special://thumbnails/%s' % image)
			kodi_utils.delete_file(removal_path)
		except: pass
	kodi_utils.sleep(200)
	kodi_utils.execute_builtin('ReloadSkin()')
	kodi_utils.sleep(500)
	kodi_utils.notification(32576)

def upload_logfile():
	# Thanks 123Venom
	if not kodi_utils.confirm_dialog(text=ls(32580), top_space=True): return
	from modules.requests_utils import make_requests
	kodi_utils.show_busy_dialog()
	requests = make_requests()
	url = 'https://paste.kodi.tv/'
	log_file = kodi_utils.translate_path('special://logpath/kodi.log')
	if not kodi_utils.path_exists(log_file): return kodi_utils.ok_dialog(text='Error. Log File Not Found.', top_space=True)
	try:
		with kodi_utils.open_file(log_file) as f: text = f.read()
		UserAgent = 'Fen %s' % kodi_utils.addon().getAddonInfo('version')
		response = requests.post(''.join([url, 'documents']), data=text.encode('utf-8', errors='ignore'), headers={'User-Agent': UserAgent}).json()
		if 'key' in response: kodi_utils.ok_dialog(text=''.join([url, response['key']]), top_space=True)
		else: kodi_utils.ok_dialog(text='Error. Log Upload Failed')
	except: kodi_utils.ok_dialog(text='Error. Log Upload Failed')
	kodi_utils.hide_busy_dialog()