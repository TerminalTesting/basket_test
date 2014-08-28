#! /usr/bin/python
# -*- coding: utf8 -*-
import unittest
import sys
import os
from models import *
from selenium import webdriver
import time
from selenium.common.exceptions import NoSuchElementException
from sqlalchemy import or_

class BasketTest(unittest.TestCase):
    """ Тест кейс для тестирования корзины """
    os.system('find -iname \*.png -delete')
    
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    SCHEMA = os.getenv('SCHEMA')
    USER = os.getenv('USER')
    PSWD = os.getenv('PSWD')
    CITY_DOMAIN = (os.getenv('CITY_DOMAIN')).decode('utf-8', 'ignore')
    ADRESS = 'http://%s.%s/' % (CITY_DOMAIN, os.getenv('SITE_DOMAIN'))
    CONNECT_STRING = 'mysql://%s:%s@%s:%s/%s?charset=utf8' %(USER, PSWD, HOST, PORT, SCHEMA)
    ARTSOURCE = '%sartifact/' % os.getenv('BUILD_URL')

    engine = create_engine(CONNECT_STRING, echo=True) #Значение False параметра echo убирает отладочную информацию
    metadata = MetaData(engine)
    session = create_session(bind = engine)

    #ищем магазин - склад
    store_shop = session.query(Shops.db_sort_field).\
              join(Region, Shops.city_id == Region.id).\
              filter(Shops.active == 1).\
              filter(Shops.flag_store_shop_kbt == 1).\
              filter(Region.domain == CITY_DOMAIN).\
              first()
    if store_shop != None:
        store_shop = store_shop[0]
    else:
        store_shop = session.query(Shops.db_sort_field).\
                         filter(Shops.id == session.query(Region.supplier_id).filter(Region.domain == CITY_DOMAIN).first()[0]).\
                         first()[0]
        
    item_mgt = session.query(Goods).\
               join(Goods_stat, Goods.id == Goods_stat.goods_id).\
               join(Region, Goods_stat.city_id == Region.id).\
               join(Goods_block, Goods.block_id == Goods_block.id).\
               join(Main_goods_prices, Goods.id == Main_goods_prices.goods_id ).\
               join(Remains, Remains.goods_id == Goods.id).\
               filter(Region.domain == CITY_DOMAIN).\
               filter(Goods_stat.status == 1).\
               filter(Goods.overall_type == 0).\
               filter(Goods_block.delivery_type == 1).\
               filter(Main_goods_prices.price_type_guid == Region.price_type_guid).\
               filter(Main_goods_prices.price > 2000).\
               filter('t_goods_remains.%s > 0' % store_shop).\
               limit(8).all()
        
    item_kgt = session.query(Goods).\
               join(Goods_stat, Goods.id == Goods_stat.goods_id).\
               join(Region, Goods_stat.city_id == Region.id).\
               join(Goods_block, Goods.block_id == Goods_block.id).\
               join(Main_goods_prices, Goods.id == Main_goods_prices.goods_id ).\
               join(Remains, Remains.goods_id == Goods.id).\
               filter(Region.domain == CITY_DOMAIN).\
               filter(Goods_stat.status == 1).\
               filter(or_(Goods.overall_type == 2, Goods_block.delivery_type == 2)).\
               filter(Main_goods_prices.price_type_guid == Region.price_type_guid).\
               filter(Main_goods_prices.price != 0).\
               filter('t_goods_remains.%s > 0' % store_shop).\
               limit(8).all()

    item_post = session.query(Goods).\
               join(Goods_stat, Goods.id == Goods_stat.goods_id).\
               join(Region, Goods_stat.city_id == Region.id).\
               join(Supplier_goods_prices, Goods.id == Supplier_goods_prices.goods_id ).\
               join(Remains, Remains.goods_id == Goods.id).\
               filter(Region.domain == CITY_DOMAIN).\
               filter(Supplier_goods_prices.price_type_guid == Region.price_type_guid).\
               filter(Supplier_goods_prices.price_supplier != 0).\
               filter(Goods_stat.status == 5).\
               limit(8).all()

    item_prefs = {0: 'Товар с обычной габаритностью', 1: 'Крупногабаритный товар', 2: 'Товар статусом поставщика'}
    
    def tearDown(self):
        """ Удаление переменных для всех тестов. Остановка приложения """
        if sys.exc_info()[0]:   
            print sys.exc_info()[0]

    def browser_start(self, term = False, auth = False):

        """ запускает браузер """
        
        if term:
            profile = webdriver.FirefoxProfile()
            profile.set_preference("general.useragent.override", "Opera/9.80 (tcode003) Presto/2.12.388 Version/12.16")
            self.driver = webdriver.Firefox(profile)
        else:
            self.driver = webdriver.Firefox()
            self.driver.get(self.ADRESS)

        if auth:
            self.driver.get('%slogin/' % self.ADRESS)
            time.sleep(5)
            self.driver.find_element_by_id('username').send_keys(os.getenv('AUTH'))
            self.driver.find_element_by_id('password').send_keys(os.getenv('AUPASS'))
            self.driver.find_element_by_class_name('btn-primary').click()
            time.sleep(5)

    def set_additional(self, items):

        """ Составляет список доп. услуг и гарантий к конкретному товару """
           
        self.additional = [[],[],[]]
           
        self.additional[0].append(self.session.query(Additional.block_id).\
                filter(Additional.goods_id == items[0].block_id).all())
        self.additional[0].append(self.session.query(Warranty.block_id).\
                filter(Warranty.goods_id == items[0].block_id).all())
        self.additional[1].append(self.session.query(Additional.block_id).\
                filter(Additional.goods_id == items[1].block_id).all())
        self.additional[1].append(self.session.query(Warranty.block_id).\
                filter(Warranty.goods_id == items[1].block_id).all())
        self.additional[2].append(self.session.query(Additional.block_id).\
                filter(Additional.goods_id == items[2].block_id).all())
        self.additional[2].append(self.session.query(Warranty.block_id).\
                filter(Warranty.goods_id == items[2].block_id).all())



    def fill_a_form(self):
        
        """ заполняет форму для неавторизованных пользователей """
        
        self.driver.find_element_by_id('personal_order_form_firstName').send_keys('AutoTEST')
        self.driver.find_element_by_id('personal_order_form_phoneNumber').send_keys('123456789')
        self.driver.find_element_by_id('personal_order_form_email').send_keys('AutoTEST@AutoTEST.test')
        self.driver.find_element_by_id('personal_order_form_comment').send_keys('AutoTEST ORDER')

    def add_item_to_cart(self, item_cnt, good):

        """ добавляет товар в корзину """
        
        self.driver.get('%sproduct/%s/' % (self.ADRESS, good.alias))#ссылка на карточку товара, который будет добавлен в корзину
        time.sleep(5)
        self.driver.find_element_by_link_text('Купить').click()
        time.sleep(5)
        order_add = '%sbasket/?a=a' % self.ADRESS
        if len(self.additional[item_cnt][1]): #если есть доп гарантия
            order_add = order_add + '&goods[%d][srv][]=%d' % (good.id, self.additional[item_cnt][1][0][0])
        if len(self.additional[item_cnt][0]): #если есть доп услуги
            order_add = order_add + '&goods[%d][srv][]=%d' % (good.id, self.additional[item_cnt][0][0][0])
        self.driver.get(order_add)
        time.sleep(5)
                       

    def test_basket_0(self):
   
        """ Тестирование веб версии сайта - пользователь не авторизован """
        stat = 0

        item_mgt = self.session.query(Goods).\
               join(Goods_stat, Goods.id == Goods_stat.goods_id).\
               join(Region, Goods_stat.city_id == Region.id).\
               join(Goods_block, Goods.block_id == Goods_block.id).\
               join(Main_goods_prices, Goods.id == Main_goods_prices.goods_id ).\
               join(Remains, Remains.goods_id == Goods.id).\
               filter(Region.domain == self.CITY_DOMAIN).\
               filter(Goods_stat.status == 1).\
               filter(Goods.overall_type == 0).\
               filter(Goods_block.delivery_type == 1).\
               filter(Main_goods_prices.price_type_guid == Region.price_type_guid).\
               filter(Main_goods_prices.price > 2000).\
               filter('t_goods_remains.%s > 0' % self.store_shop).\
               limit(8).all()
        
        item_kgt = self.session.query(Goods).\
               join(Goods_stat, Goods.id == Goods_stat.goods_id).\
               join(Region, Goods_stat.city_id == Region.id).\
               join(Goods_block, Goods.block_id == Goods_block.id).\
               join(Main_goods_prices, Goods.id == Main_goods_prices.goods_id ).\
               join(Remains, Remains.goods_id == Goods.id).\
               filter(Region.domain == self.CITY_DOMAIN).\
               filter(Goods_stat.status == 1).\
               filter(or_(Goods.overall_type == 2, Goods_block.delivery_type == 2)).\
               filter(Main_goods_prices.price_type_guid == Region.price_type_guid).\
               filter(Main_goods_prices.price != 0).\
               filter('t_goods_remains.%s > 0' % self.store_shop).\
               limit(8).all()

        item_post = self.session.query(Goods).\
               join(Goods_stat, Goods.id == Goods_stat.goods_id).\
               join(Region, Goods_stat.city_id == Region.id).\
               join(Supplier_goods_prices, Goods.id == Supplier_goods_prices.goods_id ).\
               join(Remains, Remains.goods_id == Goods.id).\
               filter(Region.domain == self.CITY_DOMAIN).\
               filter(Supplier_goods_prices.price_type_guid == Region.price_type_guid).\
               filter(Supplier_goods_prices.price_supplier != 0).\
               filter(Goods_stat.status == 5).\
               limit(8).all()
  
        items = (self.item_mgt[0], self.item_kgt[0], self.item_post[0]) #для каждого теста беруться разные товары
        self.set_additional(items)
        item_cnt = 0
        
        for good in items:

            try:    

                self.browser_start()
                self.add_item_to_cart(item_cnt, good)
                item_cnt += 1
                self.fill_a_form()
                time.sleep(5)
                self.driver.find_element_by_class_name('btn-primary').click() #Покупаем товар
                self.driver.find_element_by_class_name('order-details')
                self.driver.close()
            
            except:
                self.driver.get_screenshot_as_file('%s.png' % good.alias)
                self.driver.close()
                stat += 1
                print 'Не получилось оформить заказ без доставки у неавт. пользователя - ', good.alias
                print self.item_prefs[item_cnt-1]
                print 'Скриншот:\n', self.ARTSOURCE + '%s.png' % good.alias
                print '-'*80
    
        
        items = (self.item_mgt[1], self.item_kgt[1], self.item_post[1]) #для каждого теста беруться разные товары
        self.set_additional(items)
        item_cnt = 0

        for good in items:
            
            try:
                
                self.browser_start()
                self.add_item_to_cart(item_cnt, good)
                item_cnt += 1
                self.fill_a_form()
                time.sleep(5)
                self.driver.find_element_by_css_selector("div.dcityContainer > span.radio").click()
                self.driver.find_element_by_id('personal_order_form_addressStreet').send_keys('AutoTEST street')
                self.driver.find_element_by_id('personal_order_form_addressHouse').send_keys('AutoTEST house')
                time.sleep(5)
                self.driver.find_element_by_class_name('btn-primary').click() #Покупаем товар
                self.driver.find_element_by_class_name('order-details')
                self.driver.close()

            except:
                self.driver.get_screenshot_as_file('%s.png' % good.alias)
                self.driver.close()
                stat += 1
                print 'Не получилось оформить заказ без доставки у неавт. пользователя - ', good.alias
                print self.item_prefs[item_cnt-1]
                print 'Скриншот:\n', self.ARTSOURCE + '%s.png' % good.alias
                print '-'*80

        assert stat==0, (u'Errors:%d')%(stat)
        
    def test_basket_1(self):
        """ Тестирование веб версии сайта - пользователь авторизован """
        stat = 0
                         
        items = (self.item_mgt[2], self.item_kgt[2], self.item_post[2]) #для каждого теста беруться разные товары
        self.set_additional(items)
        item_cnt = 0
        
        for good in items:
            
            try:
                
                self.browser_start(auth=True)
                self.add_item_to_cart(item_cnt, good)
                item_cnt += 1
                self.driver.find_element_by_id('personal_order_form_comment').send_keys('AutoTEST ORDER')
                time.sleep(5)
                self.driver.find_element_by_class_name('btn-primary').click() #Покупаем товар
                self.driver.find_element_by_class_name('order-details')
                self.driver.get('%slogout' % self.ADRESS) ######## DO NOT FORGET TO PRESS LOGOUT ########
                self.driver.close()

            except:
                self.driver.get_screenshot_as_file('%s.png' % good.alias)
                self.driver.close()
                stat += 1
                print 'Не получилось оформить заказ без доставки у неавт. пользователя - ', good.alias
                print self.item_prefs[item_cnt-1]
                print 'Скриншот:\n', self.ARTSOURCE + '%s.png' % good.alias
                print '-'*80

                    
        items = (self.item_mgt[3], self.item_kgt[3], self.item_post[3]) #для каждого теста беруться разные товары
        self.set_additional(items)
        item_cnt = 0
        
        for good in items:

            try:
                
                self.browser_start(auth=True)
                self.add_item_to_cart(item_cnt, good)
                item_cnt += 1
                self.driver.find_element_by_css_selector("div.dcityContainer > span.radio").click()
                self.driver.find_element_by_id('personal_order_form_comment').send_keys('AutoTEST ORDER')
                time.sleep(5)
                self.driver.find_element_by_class_name('btn-primary').click() #Покупаем товар
                self.driver.find_element_by_class_name('order-details')
                self.driver.get('%slogout' % self.ADRESS)
                self.driver.close()

            except:
                self.driver.get_screenshot_as_file('%s.png' % good.alias)
                self.driver.close()
                stat += 1
                print 'Не получилось оформить заказ без доставки у неавт. пользователя - ', good.alias
                print self.item_prefs[item_cnt-1]
                print 'Скриншот:\n', self.ARTSOURCE + '%s.png' % good.alias
                print '-'*80
                 
        assert stat==0, (u'Errors:%d')%(stat)

    def test_basket_2(self):
        """ Тестирование терминальной версии сайта - пользователь не авторизован """
        stat = 0
        
        items = (self.item_mgt[4], self.item_kgt[4], self.item_post[4]) #для каждого теста беруться разные товары
        self.set_additional(items)
        item_cnt = 0
        
        for good in items:

            try:
                
                self.browser_start(term = True)
                self.add_item_to_cart(item_cnt, good)
                item_cnt += 1
                self.fill_a_form()
                time.sleep(5)
                self.driver.find_element_by_class_name('btn-primary').click() #Покупаем товар
                self.driver.find_element_by_class_name('order-details')
                self.driver.close()
            
            except:
                self.driver.get_screenshot_as_file('%s.png' % good.alias)
                self.driver.close()
                stat += 1
                print 'Не получилось оформить заказ без доставки у неавт. пользователя - ', good.alias
                print self.item_prefs[item_cnt-1]
                print 'Скриншот:\n', self.ARTSOURCE + '%s.png' % good.alias
                print '-'*80
               
        items = (self.item_mgt[5], self.item_kgt[5], self.item_post[5]) #для каждого теста беруться разные товары
        self.set_additional(items)
        item_cnt = 0
        
        for good in items:

            try:
                
                self.browser_start(term = True)
                self.add_item_to_cart(item_cnt, good)
                item_cnt += 1
                self.fill_a_form()
                time.sleep(5)
                self.driver.find_element_by_css_selector("div.dcityContainer > span.radio").click()
                self.driver.find_element_by_id('personal_order_form_addressStreet').send_keys('AutoTEST street')
                self.driver.find_element_by_id('personal_order_form_addressHouse').send_keys('AutoTEST house')
                time.sleep(5)
                self.driver.find_element_by_class_name('btn-primary').click() #Покупаем товар
                self.driver.find_element_by_class_name('order-details')
                self.driver.close()

            except:
                self.driver.get_screenshot_as_file('%s.png' % good.alias)
                self.driver.close()
                stat += 1
                print 'Не получилось оформить заказ без доставки у неавт. пользователя - ', good.alias
                print self.item_prefs[item_cnt-1]
                print 'Скриншот:\n', self.ARTSOURCE + '%s.png' % good.alias
                print '-'*80
            
        assert stat==0, (u'Errors:%d')%(stat)

    def test_basket_3(self):
        """ Тестирование терминальной версии сайта - пользователь авторизован """
        stat = 0
        
        items = (self.item_mgt[6], self.item_kgt[6], self.item_post[6]) #для каждого теста беруться разные товары
        self.set_additional(items)
        item_cnt = 0
        for good in items:
            
            try:
                
                self.browser_start(term = True, auth = True)
                self.add_item_to_cart(item_cnt, good)
                item_cnt += 1
                self.driver.find_element_by_id('personal_order_form_comment').send_keys('AutoTEST ORDER')
                time.sleep(5)
                self.driver.find_element_by_class_name('btn-primary').click() #Покупаем товар
                self.driver.find_element_by_class_name('order-details')
                self.driver.get('%slogout' % self.ADRESS) ######## DO NOT FORGET TO PRESS LOGOUT ########
                self.driver.close()

            except:
                self.driver.get_screenshot_as_file('%s.png' % good.alias)
                self.driver.close()
                stat += 1
                print 'Не получилось оформить заказ без доставки у неавт. пользователя - ', good.alias
                print self.item_prefs[item_cnt-1]
                print 'Скриншот:\n', self.ARTSOURCE + '%s.png' % good.alias
                print '-'*80

        items = (self.item_mgt[7], self.item_kgt[7], self.item_post[7]) #для каждого теста беруться разные товары
        self.set_additional(items)
        item_cnt = 0
        for good in items:

            try:
                
                self.browser_start(term = True, auth = True)
                self.add_item_to_cart(item_cnt, good)
                item_cnt += 1
                self.driver.find_element_by_css_selector("div.dcityContainer > span.radio").click()
                self.driver.find_element_by_id('personal_order_form_comment').send_keys('AutoTEST ORDER')
                time.sleep(5)
                self.driver.find_element_by_class_name('btn-primary').click() #Покупаем товар
                self.driver.find_element_by_class_name('order-details')
                self.driver.get('%slogout' % self.ADRESS)
                self.driver.close()

            except:
                self.driver.get_screenshot_as_file('%s.png' % good.alias)
                self.driver.close()
                stat += 1
                print 'Не получилось оформить заказ без доставки у неавт. пользователя - ', good.alias
                print self.item_prefs[item_cnt-1]
                print 'Скриншот:\n', self.ARTSOURCE + '%s.png' % good.alias
                print '-'*80
            
        
        assert stat==0, (u'Errors:%d')%(stat)
    
        

        
