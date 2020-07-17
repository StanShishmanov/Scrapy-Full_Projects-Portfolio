# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
from scotia_club_cl.items import ScotiaClubClItem

class ScotiaClubSpider(scrapy.Spider):
    name = 'scotia_club'
    allowed_domains = ['scotiaclub.cl']
    start_urls = ['https://www.scotiaclub.cl/scclubfront/categoria/mundos/descuentos']

    def parse(self, response):
        # Get all links from benefits page
        links_category_container = response.xpath('//div[@class="row mt-5"]/div[@class="col-sm-6 col-md-4 col-lg-3 pb-3 nombres"]//div[@class="container mt-2"]')

        # Iterate over all links and request parse_page() callback

        for link in links_category_container:
            # Get the discount and use it as meta in parse_page()
            discount = link.xpath('.//div[@class="col-7 pl-0 pr-2"]/h5/text()').extract_first()
            if link.xpath('./p/text()'):
                #Get the category and use it as meta in parse_page()
                categories = link.xpath('./p/text()').extract()
            else:
                categories = ""
            
            link = 'https://www.scotiaclub.cl' + link.xpath('.//div[@class="col-5 d-flex px-0"]/a/@href').extract_first()
            yield scrapy.Request(url = link, callback = self.parse_page, meta = {"Categoria": categories, "discount": discount})


    def parse_page(self, response):
        
        # A dictionary to hold all months respective digits
        month_dict = {
            'enero': "01" , 'febrero': "02", 'marzo': "03", 'abril': "04", 'mayo': "05", 'junio': "06", 
            'julio': "07", 'agosto': "08", 'septiembre': "09", 'octubre': "10", 'noviembre': "11", 'diciembre': "12"
        }
        # A dictionary to hold all months maximum days if the days are not presented as a number on a page
        months_and_days = {
            '01': "31" , '02': "29", '03': "31", '04': "30", '05': "31", '06': "30", 
            '07': "31", '08': "31", '09': "30", '10': "31", '11': "30", '12': "31"
        }
        
        # The logo of the benefit. Is a list since image_urls requires it being a list
        benefit_logo = ['https://www.scotiaclub.cl' + response.xpath('//div[@class="row"]/div[@class="col-lg-6 text-center align-self-center"]/img/@src').extract_first()]

        # A list for holding all the months found in date, if found
        # Used for fecha_de_initio and fecha_de_termino
        months_found = []

        # A list holding all the days found in the date, if found
        # Used for fecha_de_initio and fecha_de_termino
        days_found = []

        # A bool used to do another search in validity_paragraph if no proper date has been found in descripcion_del_beneficio
        valid_date_found = False

        # Company of the Benefit Program
        empresa_del_programa = "ScotiaClub"

        # Gets the name of the business from the benefit page
        nombre_del_comercio = response.xpath('//div[@class="row"]//h2/strong//text()').extract_first()

        # Gets both tipo_de_beneficio and nombre_del_beneficio from the page holding all benefits using meta
        tipo_de_beneficio = response.meta["discount"] 
        nombre_del_beneficio = response.meta["discount"]

        # The category is transfered as meta data from parse() function
        categoria = response.meta["Categoria"]

        # Gets the upper conditions paragraph from the benefit page
        condiciones_upper_paragraph = response.xpath('//div[@id="accordionEx"]//div[@id="collapseTwo2"]/div/ul/li/text()').extract()
        
        # Gets lower conditions paragraph from the benefit page
        condiciones_lower_paragraph = response.xpath('//div[@id="accordionEx"]/div[@id="accordionExample"]/div[@id="collapseTerminosYCondiciones"]/div/p//text()').extract()
        
        # Concatenate both paragraphs
        terminos_y_condiciones = condiciones_upper_paragraph + condiciones_lower_paragraph

        # Remove trailing commas
        if '.,' in terminos_y_condiciones:
            terminos_y_condiciones = terminos_y_condiciones.replace('.,', ".")
        # Remove all newlines
        if '\n' in terminos_y_condiciones:
            terminos_y_condiciones = terminos_y_condiciones.replace('\n', "")


        # Assigns empty values for both variables in case they're not available on the benefit page
        website = ""
        direcciones = ""

        # Checks/ Assigns web_comercio, if available
        if response.xpath('//div[@id="collapseThree3"]/div//a/@href'):
            website = response.xpath('//div[@id="collapseThree3"]/div//a/@href').extract_first()

        # Checks/ Assigns direcciones, if available
        if response.xpath('//div[@id="collapseThree3"]/div/ul/li[not(a)]/text()'):
            direcciones = response.xpath('//div[@id="collapseThree3"]/div/ul/li[not(a)]/text()').extract()

        # Used to do a second search for proper date in the first paragraph on the page 
        # if the first search in descripcion_del_beneficio has not provided proper results
        validity_paragraph = response.xpath('//h3[@class="h3-responsive text-center text-md-left mb-5 ml-xl-0 ml-4"]/span[2]//div//text()').extract_first()

        # "¿Cómo accedo a este beneficio?" paragraph
        como_accedo_paragraph = response.xpath('//div[@class="col-lg-5 mr-3 text-center text-md-left mt-5"]/div[@id="accordionEx"]//div[1]//div[@class="card-body"]/text()').extract_first()

        # Concatenate both paragraphs
        descripcion_del_beneficio = validity_paragraph + como_accedo_paragraph

        # Remove newlines
        descripcion_del_beneficio = descripcion_del_beneficio.replace('\n', "")

        # Assigns empty values 
        valid_until = ""
        year = ""
        date_sentence = ""

        # Iterates over condiciones_lower_paragraph to find and split the sentence by year - 2020 or 2021
        # If found assigns a true value for valid_date_found so a second search is avoided
        for sentence in condiciones_lower_paragraph:
            if '2021.' in sentence:
                date_sentence = sentence
                valid_date_found = True
            elif '2021' in sentence:
                date_sentence = sentence
                valid_date_found = True
            elif '2020.' in sentence:
                date_sentence = sentence
                valid_date_found = True
            elif '2020' in sentence:
                date_sentence = sentence
                valid_date_found = True
        
        # If a valid date is found splits the given date and assigns the year variable
        if valid_date_found:
            for date in date_sentence.split('.'):
                if '2021.' in date:
                    valid_until = date.replace('2021.', "").split()
                    year = '2021'
                elif '2021' in date:
                    valid_until = date.replace('2021', "").split()
                    year = '2021'
                elif '2020.' in date:
                    valid_until = date.replace('2020.', "").split()
                    year = '2020'
                elif '2020' in date:
                    valid_until = date.replace('2020', "").split()
                    year = '2020'
        else:
            # Otherwise seraches for date in the validity paragraph. Assigns the year and valid_until variable
            for sentence in validity_paragraph.split('.'):
                if '2020.' in sentence:
                    valid_until = sentence.replace('2020., ""').split()
                    year = '2020'

                elif '2020' in sentence:
                    valid_until = sentence.replace('2020', "").split()
                    year = '2020'

                elif '2021.' in sentence:
                        valid_until = sentence.replace('2021.', "").split()
                        year = '2021'

                elif '2021' in sentence:
                        valid_until = sentence.replace('2021', "").split()
                        year = '2021'

        # Searches for a match between the months in the month_dict and if found assigns the digit representation for the month:
        # i.e. if 'mayo' is found - '05' will be appended to monhts_found
        for word in month_dict:
            if word in valid_until:
                if word not in months_found:
                    months_found.append(month_dict[word])
        
        # Searches for digits in the valid_until variable. If found - appends them to days_found 
        # to be used in a proper date construction
        for word in valid_until:
            if word.isdigit():
                days_found.append(word)

        # Assign empty variables
        fecha_de_termino = ""
        fecha_de_initio = ""
        
        # Checks and assigns the proper date output by comparing list lengths
        # if days_found has length == 2 and months_found has length == 2:
        # a day and month are available for both fecha_de_initio and fecha_de_termino
        if days_found:
            if len(days_found) == 2 and len(months_found) == 2:
                fecha_de_initio = f'{year}-' + months_found[0] + '-' + days_found[0]
                fecha_de_termino = f'{year}-' + months_found[-1] + '-' + days_found[-1]

            # If only the length of days_found == 2 -> the same month with different start and end days is available
            elif len(days_found) == 2:
                fecha_de_initio = f'{year}-' + months_found[0] + '-' + days_found[0]
                fecha_de_termino = f'{year}-' + months_found[-1] + '-' + days_found[-1]
            
            # Otherwise one day and one month are available therefore assigns fecha_de_initio to today's date
            # and only assigns the days_found and months_found variables to fecha_de_termino
            else:
                fecha_de_initio = datetime.today().strftime('%Y-%m-%d')
                fecha_de_termino = f'{year}-' + months_found[-1] + '-' + days_found[-1]

        # If no days have been found - checks how many total days the months_found variable has and assigns it to fecha_de_termino
        else:
            fecha_de_initio = datetime.today().strftime('%Y-%m-%d')
            fecha_de_termino = f'{year}-' + months_found[-1] + '-' + months_and_days[months_found[-1]]
        
        # A dictionary consisting of all counties in Santiago, Metropolitana only
        # Used for checking if any of the directions on the page has a county listed and if found - assigns it to its proper variable
        chile_communas = {
            "Metropolitana": {
                "Santiago": [
                    "Vitacura", "Santiago", "San Ramón", "San Miguel", "San Joaquín", "Renca", "Recoleta", "Quinta Normal", "Quilicura", "Pudahuel",
                    "Providencia", "Peñalolén", "Pedro Aguirre Cerda", "Ñuñoa", "Maipú", "Macul", "Lo Prado", "Lo Espejo", "Lo Barnechea", "Las Condes", 
                    "La Reina", "La Pintana", "La Granja", "La Florida", "La Cisterna", "Independencia", "Huechuraba", "Estación Central", "El Bosque", "Conchalí",
                    "Cerro Navia", "Cerrillos"
                    ]
        }
        }

        # A list of all counties - less work while iterating
        only_santiago = chile_communas["Metropolitana"]["Santiago"]

        # A list used to hold directions where ':' sign is removed. Since some counties have a trailing ':' and some don't - removes it
        clean_direcciones = []
        
        # Remove the ':' sign
        if direcciones:
            for i in direcciones:
                if ':' in i:
                    clean_direcciones.append(i.replace(':', ""))
                else:
                    clean_direcciones.append(i)

        # Assigns empty values
        county_name = ""
        email = ""
        city = ""
        region = ""
        pais = "Chile"
        phone = ""

        # Assigns the item which will hold the variable containers
        item = {}

        # A dictionary to hold the key: values of the images 
        images = {}

        # If there are any directions in clean directions - a search for a county and a phone number will be done
        if clean_direcciones:
            for direccion in clean_direcciones:

                # Assigns the items container
                item = ScotiaClubClItem()
                
                phone = ""
                county_name = ""
                city = ""
                region = ""
                # Searches for and assigns a phone number. Removes a trailing slash '/' and the phone number from the direction variable
                if "Teléfono" in direccion:
                    phone = direccion.split('Teléfono')[1].replace('.', '')
                    direccion = direccion.split('Teléfono')[0]
                    direccion = direccion.replace('/', '')

                # Used to hold counties, if found
                counties_found = []

                # Used to check if a county == "Santiago". If it is and there is another county found:
                # The county is assigned as a county name and "Santiago" as the city name
                # If "Santiago" is found and no more counties are found - "Santiago" is assigned as both county and city names
                # Also the region name is changed to "Metropolitana" 
                santiago_found = False
                for county in only_santiago:
                    if county in direccion:
                        if county == 'Santiago':
                            santiago_found = True
                        else:
                            counties_found.append(county)
                if len(counties_found) == 1:
                        county_name = counties_found[0]
                        city = "Santiago"
                        region = "Metropolitana"
                elif len(counties_found) == 0 and santiago_found:
                    county_name = "Santiago"
                    city = "Santiago"
                    region = "Metropolitana"
                elif len(counties_found) >= 2:
                    city = "Santiago"
                    region = "Metropolitana"

                # Assign and yield the results with the listed and cleaned directions
                # Check and remove if \t chars are available since they can cause an error in scrapy ( twisted ) engine
                if '\t' in nombre_del_comercio:
                    nombre_del_comercio = nombre_del_comercio.replace('\t', "")
                images['url'] = benefit_logo
                images['name'] = nombre_del_comercio
                item['image_urls'] = images
                item["nombre_del_beneficio"] = nombre_del_beneficio
                item["tipo_de_beneficio"] = tipo_de_beneficio
                item["descripcion_del_beneficio"] = descripcion_del_beneficio
                item["nombre_del_comercio"] = nombre_del_comercio
                item["descripcion_del_comercio"] = categoria
                item["terminos_y_condiciones_del_beneficio"] = terminos_y_condiciones
                item["programa_de_beneficios"] = "Scotia Club"
                item["empresa_del_programa"] = empresa_del_programa
                item["fecha_de_initio"] = fecha_de_initio
                item["fecha_de_termino"] = fecha_de_termino
                item["url_beneficio"] = response.url
                item["categoria"] = categoria
                item["web_comercio"] = website
                item['telephono_comercio'] = phone
                item['email'] = email
                item["direccion_comercio"] = direccion
                item["county_name"] = county_name
                item["city"] = city
                item["region"] = region
                item["pais"] = pais
                yield item
        else:
            item = ScotiaClubClItem()
            # Since no directions are listed on the page - yield the results without directions ( county name, city, region )
            images['url'] = benefit_logo
            images['name'] = nombre_del_comercio
            item['image_urls'] = images
            item["nombre_del_beneficio"] = nombre_del_beneficio
            item["tipo_de_beneficio"] = tipo_de_beneficio
            item["descripcion_del_beneficio"] = descripcion_del_beneficio
            item["nombre_del_comercio"] = nombre_del_comercio
            item["descripcion_del_comercio"] = categoria
            item["terminos_y_condiciones_del_beneficio"] = terminos_y_condiciones
            item["programa_de_beneficios"] = "Scotia Club"
            item["empresa_del_programa"] = empresa_del_programa
            item["fecha_de_initio"] = fecha_de_initio
            item["fecha_de_termino"] = fecha_de_termino
            item["url_beneficio"] = response.url
            item["categoria"] = categoria
            item["web_comercio"] = website
            item['telephono_comercio'] = ""
            item["direccion_comercio"] = ""
            item["county_name"] = ""
            item["city"] = ""
            item["region"] = ""
            item["pais"] = pais
            yield item