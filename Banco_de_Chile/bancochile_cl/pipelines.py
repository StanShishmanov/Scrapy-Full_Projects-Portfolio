# -*- coding: utf-8 -*-
import scrapy
from scrapy.exporters import CsvItemExporter
from scrapy import signals
from pydispatch import dispatcher
from scrapy.pipelines.images import ImagesPipeline

class BancochileClPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.file = open('Banco_de_Chile.csv', 'w+b')
        self.exporter = CsvItemExporter(self.file)
        self.exporter.fields_to_export = ['nombre_del_beneficio','tipo_de_beneficio','descripcion_del_beneficio','nombre_del_comercio','descripcion_del_comercio','terminos_y_condiciones_del_beneficio','programa_de_beneficios','empresa_del_programa','fecha_de_initio','fecha_de_termino', 'url_beneficio', 'categoria', 'web_comercio', 'telephono_comercio', 'email', 'direccion_comercio', 'county_name', 'city', 'region', 'pais']
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
class CustomImageNamePipeline(ImagesPipeline):


    def get_media_requests(self, item, info):
        my_dict = item.get('image_urls')
        url = my_dict['url'][0]
        name = my_dict["name"]
        yield scrapy.Request(url = my_dict['url'][0], meta={'image_name': my_dict["name"]})

    def file_path(self, request, response=None, info=None):
        return '%s.jpg' % request.meta['image_name']