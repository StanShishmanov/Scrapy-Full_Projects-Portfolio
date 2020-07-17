# -*- coding: utf-8 -*-
import scrapy


class BancochileClItem(scrapy.Item):
    image_urls = scrapy.Field()
    image_name = scrapy.Field()
    images = scrapy.Field()
    nombre_del_beneficio = scrapy.Field()
    tipo_de_beneficio = scrapy.Field()
    descripcion_del_beneficio = scrapy.Field()
    nombre_del_comercio = scrapy.Field()
    descripcion_del_comercio = scrapy.Field()
    terminos_y_condiciones_del_beneficio = scrapy.Field()
    programa_de_beneficios = scrapy.Field()
    empresa_del_programa = scrapy.Field()
    fecha_de_initio = scrapy.Field()
    fecha_de_termino = scrapy.Field()
    url_beneficio = scrapy.Field()
    categoria = scrapy.Field()
    web_comercio = scrapy.Field()
    telephono_comercio = scrapy.Field()
    email = scrapy.Field()
    direccion_comercio = scrapy.Field()
    county_name = scrapy.Field()
    city = scrapy.Field()
    region = scrapy.Field()
    pais = scrapy.Field()
