# -*- coding: utf-8 -*-
import re
import scrapy
from bancochile_cl.items import BancochileClItem
from datetime import datetime
from fuzzywuzzy import process
from itertools import zip_longest


class BancoChileSpider(scrapy.Spider):

    # Name of the spider
    name = 'banco_chile'
    allowed_domains = ['bancochile.cl']
    
    # The 6 links holding all the required benefits
    start_urls = [
        'https://ww3.bancochile.cl/wps/wcm/connect/Personas/Portal/programa-travel/beneficios/vestuario-calzado/',
        "https://ww3.bancochile.cl/wps/wcm/connect/personas/portal/programa-travel/beneficios/salud-y-belleza/portada",
        "https://ww3.bancochile.cl/wps/wcm/connect/personas/portal/programa-travel/beneficios/hogar/hogar",
        "https://ww3.bancochile.cl/wps/wcm/connect/personas/portal/programa-travel/beneficios/servicios/portada",
        'https://ww3.bancochile.cl/wps/wcm/connect/personas/portal/programa-travel/panoramas/restaurantes/portada',
        "https://ww3.bancochile.cl/wps/wcm/connect/personas/portal/programa-travel/panoramas/entretencion/portada"
        ]
    # Iterates over all start urls
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={"from_url": url})

    # Creates absolute links for parse_page to crawl, extract and output
    # Gets the category name and passes it the parse_page as meta  
    def parse(self, response):

        from_url = response.meta['from_url']
        base_url = 'https://ww3.bancochile.cl'

        # Restaurantes benefits has different html structure so the url must be checked first
        if from_url == 'https://ww3.bancochile.cl/wps/wcm/connect/personas/portal/programa-travel/panoramas/restaurantes/portada':
            links = response.xpath('//div[@class="content"]/div/a/@href').extract()
        else:
            links = response.xpath('//div[@class="benef-cont"]/a/@href').extract()

        # The category to be transfered as meta data to parse_page()
        categoria = response.xpath('//head/title/text()').extract_first()

        for i in links:
            # A URL from the bancochile website for buying tickets. Irrelevant to the other pages for scraping
            cine_url_to_avoid = "/wps/wcm/connect/personas/portal/programa-travel/panoramas/entretencion/cines"
            if i == cine_url_to_avoid:
                continue
            else:
                url = base_url + i
                yield scrapy.Request(url = url, callback=self.parse_page, meta={"Categoria": categoria})


    def parse_page(self, response):
        
        # TODO Logo for banco de chile
        pais = "Chile"

        # The logo of the benefit. Is a list since image_urls requires it being a list
        benefit_logo = ['https://ww3.bancochile.cl' + response.xpath('//div[@class="content"]/div[@class="content-left"]//@src').extract_first()]

        # Regex patterns to match available phone numbers. Since there are different possibilities of written numbers, 
        # different patterns are implemented and compiled as one
        phone_regex = re.compile(r'(\d{11})|(\d{10})|(\d{9})|(\d{8})|(\d\s\d{8})|(\d{2}\s\d{7})|(\+\d{2}\-\d\-\s\d{4}\-\d{4})|(\d{3}\s\d{6})|(\(\d\)\d{8})|(\d{5}\s\d{4})|(\(\+\d{3}\)\s\d{8})|(\(\+\d{4}\)\s\d{4}\s\d{3})|(\(\+\d{4}\)\s\d{3}\s\d{4})|(\+\d{3}\s\d{8})|(\(\+\d{4}\)\s\d{3}\s\d{3})|(\+\d{2}\-\d{2}\-\d{6})|(\+\d{2}\-\d{2}\-\d{7})|(\+\d{2}\-\d{2}\-\d{3}\-\d{2}\-\d{2})|(\+\d{2}\-\d{2}\-\d{3}\-\d{4})|(\(\+\d{3}\)\s\d{4}\s\d{4})|(\+\d{2}\-\d\-\d{4}\-\d{4})|(\+\d{2}\-\d{2}\-\d{3}\-\d{3})|(\(\d\)\d{8})|(\d{5}\s\d{4})|(\d{2}\-\d{3}\-\d{3})|(\+\d{2}\-\d{2}\–\d{6})|(\d{3}\s\d{4}\s\d{4})|(\+\d{2}\s\d\s\d{4}\s\d{4})')
        
        # Create a dictionary with each month and its corresponding number 
        # Will be used if a month is located anywhere in the "Valid until" text and substituted with its number so the date in 
        # starting and ending columns is properly outputted
        month_dict = {
            'enero': "01" , 'febrero': "02", 'marzo': "03", 'abril': "04", 'mayo': "05", 'junio': "06", 
            'julio': "07", 'agosto': "08", 'septiembre': "09", 'octubre': "10", 'noviembre': "11", 'diciembre': "12"}
        # Exctract the name of the benefit
        nombre_del_beneficio = response.xpath('//h3//text()').extract()

        # We get the name of the business from the url 
        nombre_del_comercio = response.url.split('/')[-1]

        # Extract the retailer decription
        descripcion_del_comercio = response.xpath('//section[@class="section-grey benef-ficha"]/a/text()').extract_first()
        if response.xpath('//div[@class="content-right"]/div/div[@class="ConDescu"]'):
            terminos_y_condiciones_del_beneficio = response.xpath('//div[@class="content-right"]/div/div/ul/li//text()').extract()
           
        else:
            terminos_y_condiciones_del_beneficio = response.xpath('//div[@class="content-right"]/ul/li//text()').extract()

        # Extracts the whole paragraph ( to search for a percentage sign - % ). If unavailable - assigns the terminos_y_condiciones to it
        if not response.xpath('//div[@class="content-right"]/p//text()'):
            percentage_paragraph = terminos_y_condiciones_del_beneficio
        else:
            percentage_paragraph = response.xpath('//div[@class="content-right"]/p//text()').extract()
        
        # Get the terminos y condiciones text 
        # Also to search for % sign or email below in the iteration
        email = ""
        
        # Assign an empty string variable for the type of benefit
        tipo_de_beneficio = ""

        # Assign an empty string for the retail website URL 
        web_comercio = ""
        # String searching is implemented below so the index of the % sign is needed if found
        index_of_percent = 0
        first_index = 0
        
        # Iterate over the name of the benefit, the paragraph and the unordered list to search for the % sign
        # If found in any of them, extract 2 previous indexes to get the whole number % - 20%, 50% etc.
        # Or if "Dólares-Premio" found in any of them it will be assigned as tipo_de_beneficio
        tipo_found = False
        for i,j,k in zip_longest(nombre_del_beneficio, percentage_paragraph, terminos_y_condiciones_del_beneficio):
            if i:
                if '%' in i:
                    tipo_found = True
                    index_of_percent = i.index('%')
                    first_index = index_of_percent - 2
                    tipo_de_beneficio = str(i[first_index: index_of_percent + 1]) + " de descuento"
                elif "Dólares-Premio" in i:
                    tipo_found = True
                    tipo_de_beneficio = nombre_del_beneficio
            if not tipo_found:
                if j:
                    if '%' in j:
                        tipo_found = True
                        index_of_percent = j.index('%')
                        first_index = index_of_percent - 2
                        tipo_de_beneficio = str(j[first_index: index_of_percent + 1]) + " de descuento"
                    elif "Dólares-Premio" in j:
                        tipo_found = True
                        tipo_de_beneficio = nombre_del_beneficio
            if not tipo_found:
                if k:
                    if '%' in k:
                        tipo_found = True
                        index_of_percent = k.index('%')
                        first_index = index_of_percent - 2
                        tipo_de_beneficio = str(k[first_index: index_of_percent + 1]) + " de descuento"
                    elif "Dólares-Premio" in k:
                        tipo_found = True
                        tipo_de_beneficio = nombre_del_beneficio

        # Iterate over all of the 3 for a website URL
        # Iterate over the name of the benefit, the paragraph and the unordered list to search for the website
        # If found in any - the string will be split so only the website is extracted
        # Assign it to its variable accordingly afterwards
        for i,j,k in zip_longest(nombre_del_beneficio, percentage_paragraph, terminos_y_condiciones_del_beneficio):
            if i:
                if 'www' in i:
                    new_list = i.split()
                    for string in new_list:
                        if 'www' in string:
                            web_comercio = string
            elif j:
                if 'www' in j:
                    new_list = j.split()
                    for string in new_list:
                        if 'www' in string:
                            web_comercio = string
            elif k:
                if 'www' in k:
                    new_list = k.split()
                    for string in new_list:
                        if 'www' in string:
                            web_comercio = string

        # Exctract the benefit description and remove trailing newlines and whitespaces from the string
        descripcion_del_beneficio = response.xpath('//div[@class="content-bottom"]/p//text()').extract_first().strip()

        # Find where in descripcion_del_beneficio is the first '2020' or '2021' located. It is the only constant found in each benefit's description string
        # Split the descripcion_del_beneficio on '2020' or on '2021' and take the first part
        year = ""
        promocion_valida = ""
        if '2020' in descripcion_del_beneficio:
            promocion_valida = descripcion_del_beneficio.split('2020')[0]
            year = '2020'
        elif '2021'in descripcion_del_beneficio:
            promocion_valida = descripcion_del_beneficio.split('2021')[0]
            year = '2021'
        # Check for 'desde ' - if found - there is a starting date. So far there are only 2 possiblities listed on the website for the promocion_valida string:
        # Either it has 'desde ' or it has 'hasta ' so we search for either one of them
        # If 'desde' is found - split the string on it, take the second part and make a list out of it for iteration below
        if 'desde ' in promocion_valida:
            promocion_valida = promocion_valida.split('desde ')[1].split()
        
        # If 'hasta ' is found - split the string on it, take the second part and make a list out of it for iteration below
        elif 'hasta ' in promocion_valida:
            promocion_valida = promocion_valida.split('hasta ')[1].split()

        # Search for 'el', 'al', 'de' and 'del' keywords and if found - remove them so only the actual dates are left in the list( promocion_valida )
        for i in promocion_valida:
            if 'el' in promocion_valida:
                promocion_valida.remove('el')
            elif 'al' in promocion_valida:
                promocion_valida.remove('al')
            elif 'de' in promocion_valida:
                promocion_valida.remove('de')
            elif 'del' in promocion_valida:
                promocion_valida.remove('del')

        # Substitute each month found in promocion_valida list with its corresponding number
        for k, v in month_dict.items():
            if k in promocion_valida:
                subs = promocion_valida.index(k)
                promocion_valida[subs] = str(month_dict[k])

        # Assign fetcha_de_initio to today's date. If another starting date is found in the promocion valida list, this will be substituted.
        fecha_de_initio = datetime.today().strftime('%Y-%m-%d')
        fecha_de_termino = ""

        # Checks the length of promocion valida:
        # If the length == 4 then there is a month for fecha_de_initio and a month for fecha_de_termino
        # If the length == 3 then both fecha_de_initio and fecha_de_termino have the same month
        # If the length == 2, fecha_de_initio stays set to today's date and only fecha_de_termino is set according to the benefit's information
        if len(promocion_valida) == 2:
            fecha_de_termino = f'{year}-' + promocion_valida[1] + '-' + promocion_valida[0]
        elif len(promocion_valida) == 3:
            fecha_de_initio = f'{year}-' + promocion_valida[2] + '-' + promocion_valida[0]
            fecha_de_termino = f'{year}-' + promocion_valida[2] + '-' + promocion_valida[1]
        elif len(promocion_valida) == 4:
            fecha_de_initio = f'{year}-' + promocion_valida[1] + '-' + promocion_valida[0]
            fecha_de_termino = f'{year}-' + promocion_valida[3] + '-' + promocion_valida[2]

        # Extract the type of program
        programa_de_beneficios = response.xpath('//div[@class="navbar-header"]//img/@title').extract_first()
        # Company of the Benefit Program
        empresa_del_programa = "Banco de Chile"

        # A nested dictionary holding all counties with their respective cities and regions in Chile
        chile_communas = {
            "Arica and Parinacota": {
                "Arica": ["Camarones", "Arica"],
                "Parinacota": ["Putre", "General Lagos"]
            },
            "Tarapacá": {
                "Iquique": ["Iquique", "Alto Hospicio"],
                "Tamarugal": ["Pozo Almonte", "Pica", "Huara", "Colchane", "Camiña"]
            },
            "Antofagasta": {
                "Antofagasta": ["Taltal", "Sierra Gorda", "Mejillones", "Antofagasta"],
                "El Loa": ["San Pedro de Atacama", "Ollagüe", "Calama"],
                "Tocopilla": ["Tocopilla", "María Elena"]
            },
            "Atacama": {
                "Chañaral": ["Diego de Almagro", "Chañaral"],
                "Copiapó": ["Tierra Amarilla", "Copiapó", "Caldera"],
                "Huasco": ["Vallenar", "Huasco", "Freirina", "Alto del Carmen"]
            },
            "Coquimbo": {
                "Choapa": ["Salamanca", "Los Vilos", "Illapel", "Canela"],
                "Elqui": ["Vicuña", "Paiguano", "La Serena", "La Higuera", "Coquimbo", "Andacollo"],
                "Limarí": ["Río Hurtado", "Punitaqui", "Ovalle", "Monte Patria", "Combarbalá"]
            },
            "Valparaíso": {
                "Isla de Pascua": ["Isla de Pascua"],
                "Los Andes": ["San Esteban", "Rinconada", "Los Andes", "Calle Larga"],
                "Marga Marga": ["Villa Alemana", "Quilpué", "Limache", "Olmué"],
                "Petorca": ["Zapallar", "Petorca", "Papudo", "La Ligua", "Cabildo"],
                "Quillota": ["Quillota", "Nogales", "La Cruz", "La Calera", "Hijuelas"],
                "San Antonio": ["Santo Domingo", "San Antonio", "El Tabo", "El Quisco", "Cartagena", "Algarrobo"],
                "San Felipe": ["Santa María", "San Felipe", "Putaendo", "Panquehue", "Llaillay", "Catemu"],
                "Valparaíso": ["Viña del Mar", "Valparaíso", "Quintero", "Puchuncaví", "Concón", "Juan Fernández", "Casablanca"]
            },
            "Metropolitana": {
                "Chacabuco": ["Tiltil", "Lampa", "Colina"],
                "Cordillera": ["San José de Maipo", "Puente Alto", "Pirque"],
                "Maipo": ["San Bernardo", "Paine", "Calera de Tango", "Buin"],
                "Melipilla": ["San Pedro", "Melipilla", "María Pinto", "Curacaví", "Alhué"],
                "Santiago": [
                    "Vitacura", "Santiago", "San Ramón", "San Miguel", "San Joaquín", "Renca", "Recoleta", "Quinta Normal", "Quilicura", "Pudahuel",
                    "Providencia", "Peñalolén", "Pedro Aguirre Cerda", "Ñuñoa", "Maipú", "Macul", "Lo Prado", "Lo Espejo", "Lo Barnechea", "Las Condes", 
                    "La Reina", "La Pintana", "La Granja", "La Florida", "La Cisterna", "Independencia", "Huechuraba", "Estación Central", "El Bosque", "Conchalí",
                    "Cerro Navia", "Cerrillos"
                    ],
                "Talagante":["Talagante", "Peñaflor", "Padre Hurtado", "Isla de Maipo", "El Monte"]
            },
            "O'Higgins": {
                "Cachapoal": [
                    "San Vicente", "Requínoa", "Rengo", "Rancagua", "Quinta de Tilcoco", "Pichidegua", "Peumo", "Olivar", "Mostazal", 
                    "Malloa", "Machalí", "Las Cabras", "Graneros", "Doñihue", "Coltauco", "Coinco", "Codegua"
                    ],
                "Cardenal Caro": ["Pichilemu", "Paredones", "Navidad", "Marchihue", "Litueche", "La Estrella"],
                "Colchagua": ["Santa Cruz", "San Fernando", "Pumanque", "Placilla", "Peralillo", "Palmilla", "Nancagua", "Lolol", "Chimbarongo", "Chépica"]
            },
            "Maule": {
                "Cauquenes": ["Pelluhue", "Chanco", "Cauquenes"],
                "Curicó": ["Vichuquén", "Teno", "Sagrada Familia", "Romeral", "Rauco", "Molina", "Licantén", "Hualañé", "Curicó"],
                "Linares": ["Yerbas Buenas", "Villa Alegre", "San Javier", "Retiro", "Parral", "Longaví", "Linares", "Colbún"],
                "Talca": ["Talca", "San Rafael", "San Clemente", "Río Claro", "Pencahue", "Pelarco", "Maule", "Empedrado", "Curepto", "Constitución"]
            },
            "Ñuble": {
                "Diguillín": ["Chillán Viejo", "Chillán", "Bulnes", "El Carmen", "Pemuco", "Pinto", "Quillón", "San Ignacio", "Yungay"],
                "Itata": ["Cobquecura", "Coelemu", "Ninhue", "Portezuelo", "Quirihue", "Ránquil", "Treguaco"],
                "Punilla": ["Coihueco", "Ñiquén", "San Carlos", "San Fabián", "San Nicolás"]
            },
            "Biobío": {
                "Arauco": ["Tirúa", "Los Álamos", "Lebu", "Curanilahue", "Contulmo", "Cañete", "Arauco"],
                "Biobío": [
                    "Yumbel", "Tucapel", "Santa Bárbara", "San Rosendo", "Quilleco", "Quilaco", "Negrete", 
                    "Nacimiento", "Mulchén", "Los Ángeles", "Laja", "Cabrero", "Antuco", "Alto Biobío"
                    ],
                "Concepción": [
                    "Tomé", "Talcahuano", "Santa Juana", "San Pedro de la Paz", "Penco", "Lota", 
                    "Hualqui", "Hualpén", "Florida", "Coronel", "Concepción", "Chiguayante"
                    ]
            },
            "Araucanía": {
                "Cautín": [
                    "Villarrica", "Vilcún", "Toltén", "Teodoro Schmidt", "Temuco", "Saavedra", "Pucón", 
                    "Pitrufquén", "Perquenco", "Padre Las Casas", "Nueva Imperial", "Melipeuco", "Loncoche", "Lautaro",
                    "Gorbea", "Galvarino", "Freire", "Curarrehue", "Cunco", "Cholchol", "Carahue"
                    ],
                "Malleco": ["Victoria", "Traiguén", "Renaico", "Purén", "Lumaco", "Los Sauces", "Lonquimay", "Ercilla", "Curacautín", "Collipulli", "Angol"],
            },
            "Los Ríos": {
                "Ranco": ["Río Bueno", "Lago Ranco", "La Unión", "Futrono"],
                "Valdivia": ["Valdivia", "Panguipulli", "Paillaco", "Mariquina", "Máfil", "Los Lagos", "Lanco", "Corral"]
            },
            "Los Lagos": {
                "Chiloé": ["Quinchao", "Quemchi", "Quellón", "Queilén", "Puqueldón", "Dalcahue", "Curaco de Vélez", "Chonchi", "Castro", "Ancud"],
                "Llanquihue": ["Puerto Varas", "Puerto Montt", "Maullín", "Los Muermos", "Llanquihue", "Frutillar", "Fresia", "Cochamó", "Calbuco"],
                "Osorno": ["San Pablo", "San Juan de la Costa", "Río Negro", "Puyehue", "Purranque", "Puerto Octay", "Osorno"],
                "Palena": ["Palena", "Hualaihué", "Futaleufú", "Chaitén"]
            },
            "Aysén": {
                "Aysén": ["Guaitecas", "Cisnes", "Aysén"],
                "Capitán Prat": ["Tortel", "O'Higgins", "Cochrane"],
                "Coyhaique": ["Lago Verde", "Coihaique"],
                "General Carrera": ["Río Ibáñez", "Chile Chico"]
            },
            "Magallanes": {
                "Antártica Chilena": ["Cabo de Hornos", "Antártica"],
                "Magallanes": ["San Gregorio", "Río Verde", "Punta Arenas", "Laguna Blanca"],
                "Tierra del Fuego": ["Timaukel", "Primavera", "Porvenir"],
                "Última Esperanza": ["Torres del Paine", "Natales"]
            }

        }

        all_cities = []
        # Gets all cities in a list for lighter search
        for d1, d2 in chile_communas.items():
            for k, v in d2.items():
                all_cities.append(k)

        # Gets the html directions box
        direction_box = ""
        if response.xpath('//div[@class="contBlokAcordeon"]'):
            direction_box = response.xpath('//div[@class="contBlokAcordeon"]')

        # Checks how many "Direcciones" are listed so one can iterate over them - usually one or two ( ex. Santiago, Regiones )
        # Gets the direction name to run a light city search instead of full - i.e. if "Santiago" --> get it's counties and only iterate over them
        first_direction_name = ""
        first_direction_box = ""
        second_direction_name = ""
        second_direction_box = ""
        if direction_box:
            
            if len(direction_box) == 1:
                first_direction_box = direction_box[0].xpath('.//ul/li')
                first_direction_name = direction_box[0].xpath('./div[@class="ContTitulo"]/h2/text()').extract_first() # Get the first name ( ex Santiago )
            elif len(direction_box) == 2:
                first_direction_box = direction_box[0].xpath('.//ul/li')
                first_direction_name = direction_box[0].xpath('./div[@class="ContTitulo"]/h2/text()').extract_first()
                second_direction_box = direction_box[1].xpath('.//ul/li')
                second_direction_name = direction_box[1].xpath('./div[@class="ContTitulo"]/h2/text()').extract_first() # Get the second name (ex. Regiones )

        # Assign an empty value for a city
        city_found = False
        # A list to check how many cities match the search below
        total_cities_found = []
        # A list to hold the addresses
        address_list = []
        # A dictionary to hold the counties if a city is matched
        my_dict = {}
        
        # Checks if "Direcciones" exists on the page
        if first_direction_name:

            # Assigns addresses and strips them of empty spaces
            for i in first_direction_box:
                address = i.xpath('.//text()').extract()
                address = [j.strip() for j in address]
                address_list.append(address)

            # Flattens the nested lists and concatenate the strings in the addresses lists so the phone numbers correspond to their listed address
            joined_list = [' '.join(x) for x in address_list]

            # A list of words for string matching
            phone_words = ["Teléfono:" , "Reservas al fono", "Teléfono", "Reservas:", "Reservas al", "Reservas", "Tel"]

            # Creates a dictionary to add the address with it's corresponding number if available
            address_phone_dict = {}

            # Used below to check if a city is matched
            city_match = ""

            # Checks for a phone-related word and website - if found - gets the phone number and/ or website name
            for word in phone_words:
                for address in joined_list:

                    # Checks for a website
                    if 'www' in address:
                            web_comercio = address
                            joined_list.remove(address)
                    else:
                        if word in address:
                            address_only = address.split(word)[0]
                            phone = address.split(word)[1]
                            joined_list.remove(address)
                            cleaned_phone_number = phone.replace("(", "").replace(")", "").replace("+", "").replace("-","").replace(":", "")
                            if address_only not in address_phone_dict.keys():
                                address_phone_dict[address_only] = cleaned_phone_number
                            
            # Checks for a phone regex match if the previous for loop didn't missed a match
            for address in joined_list:
                # Searches through all the addresses
                phone_number = ""

                # Search for a matching regex pattern for a phone number 
                # If a matching regex is found - assigns it as the value to the address key in the address_phone_dict
                # Checks to see if the "Local" keyword exists right before the found number to avoid writing part of the address
                # i.e. Local A200-A202-A204
                # (?<!Local\s)(\(\+\d{4}\)\s\d{3}\s\d{4})
                r1 = re.search(phone_regex, address)

                if r1:
                    phone_number = str(r1.group()) # Assigns phone number
                    start_phone_index = r1.span()[0]
                    end_phone_index = r1.span()[1]
                    
                    # Checks to see if the match is a part of a "Local" address
                    # If found - removes the match and searches again
                    if "Local" in address[start_phone_index - 10: end_phone_index] or "local" in address[start_phone_index - 10: end_phone_index]:
                        string_to_check = address[: start_phone_index] + address[end_phone_index:]
                        r2 = re.search(phone_regex, string_to_check)

                        # If there is a second match without the local part - it should take the phone number
                        if r2:
                            phone_number = str(r2.group())
                            new_address = address.replace(phone_number, "").strip(' .')
                            cleaned_phone_number = phone_number.replace("(", "").replace(")", "").replace("+", "").replace("-","").replace(":", "") # Removes dashes, brackets and plus signs
                            address_phone_dict[new_address] = cleaned_phone_number

                        else:
                            phone_number = ""
                            address_phone_dict[address] = phone_number
                    else:
                        new_address = address.replace(phone_number, "").strip(' .') # Removes the phone number from the whole string and the trailing dot if available
                        cleaned_phone_number = phone_number.replace("(", "").replace(")", "").replace("+", "").replace("-","").replace(":", "") # Removes dashes, brackets and plus signs
                        address_phone_dict[new_address] = cleaned_phone_number
                    
                # If unavailable leaves the phone value empty 
                else:
                    phone_number = "" # Assign an empty phone number field
                    address_phone_dict[address] = phone_number # Add it to the dictionary
                
                # Runs a search with the "Direcciones" string to find a matching city in the chile_communas dictionary
                # If a mathing city is found - gets it's name so a lighter search can be done below
                if process.extractOne(first_direction_name, all_cities, score_cutoff=90): # Tries string matching, score_cutoff=90 is the best match possible
                    total_cities_found.append(process.extractOne(first_direction_name, all_cities, score_cutoff=90)) # Assigns name if match is found 
                """    
                # Checks the length of the total_cities in the list - if only one city is found - sets the city_found boolean to true
                # This is done to assure the list will not be either empty or that it has more than one city to it
                # If it has more than one city - no county, city or region will be output in the csv to avoid presenting wrong information
                """
                if len(total_cities_found) == 1:
                    city_found = True
                    city_match = total_cities_found[0][0] # Assign the matched city to a variable
            if city_found:
                
                """
                # Gets the Region, City and it's counties
                # If nested dictionary key ( city ) matches the above city's name - assigns it's region, city and it's counties to a new dictionary,
                # which will be used to perform a lighter search below
                """

                for d1, d2 in chile_communas.items(): # Iterate over the dictionary regions and cities
                    for key, value in d2.items(): # Iterates over the nested dictionary ( cities ) and their counties
                        if key == city_match: 
                            region = d1
                            city = key
                            my_dict[d1] = {}
                            my_dict[d1][key] = value

                # Iterates over the new dictionary to assign only the counties in a list
                counties = []
                for d1, d2 in my_dict.items():
                    for k, v in d2.items():
                        counties = v

                # Assign a new dictionary for the csv output
                scraped_info = {}

                # Iterates over the address_phone_dict to compare and match counties
                # If a match is found - the county is added to the output, otherwise it's left empty
                for key, value in address_phone_dict.items():
                    item = BancochileClItem()
                    if process.extractOne(key, counties, score_cutoff=90):
                        county_found = process.extractOne(key, counties, score_cutoff=90)
                        county_name = county_found[0]
            
                        images = {}

                        images['url'] = benefit_logo 
                        images['name'] = nombre_del_comercio
                        item['image_urls'] = images
                        item['nombre_del_beneficio'] = nombre_del_beneficio
                        item['tipo_de_beneficio'] = tipo_de_beneficio
                        item['descripcion_del_beneficio'] = descripcion_del_beneficio
                        item['nombre_del_comercio'] = nombre_del_comercio
                        item['descripcion_del_comercio'] = descripcion_del_comercio
                        item['terminos_y_condiciones_del_beneficio'] = terminos_y_condiciones_del_beneficio
                        item['programa_de_beneficios'] = programa_de_beneficios
                        item['empresa_del_programa'] = empresa_del_programa
                        item['fecha_de_initio'] = fecha_de_initio
                        item['fecha_de_termino'] = fecha_de_termino
                        item['url_beneficio'] = response.url
                        item['categoria'] = response.meta['Categoria']
                        item['web_comercio'] = web_comercio
                        item['telephono_comercio'] = value
                        item['email'] = email
                        item['direccion_comercio'] = key
                        item['county_name'] = county_name
                        item['city'] = city
                        item['region'] = region
                        item['pais'] = pais
                        yield item

                    else:                        
                        images = {}

                        images['url'] = benefit_logo 
                        images['name'] = nombre_del_comercio
                        item['image_urls'] = images
                        item['nombre_del_beneficio'] = nombre_del_beneficio
                        item['tipo_de_beneficio'] = tipo_de_beneficio
                        item['descripcion_del_beneficio'] = descripcion_del_beneficio
                        item['nombre_del_comercio'] = nombre_del_comercio
                        item['descripcion_del_comercio'] = descripcion_del_comercio
                        item['terminos_y_condiciones_del_beneficio'] = terminos_y_condiciones_del_beneficio
                        item['programa_de_beneficios'] = programa_de_beneficios
                        item['empresa_del_programa'] = empresa_del_programa
                        item['fecha_de_initio'] = fecha_de_initio
                        item['fecha_de_termino'] = fecha_de_termino
                        item['url_beneficio'] = response.url
                        item['categoria'] = response.meta['Categoria']
                        item['web_comercio'] = web_comercio
                        item['telephono_comercio'] = value
                        item['email'] = email
                        item['direccion_comercio'] = key
                        item['county_name'] = ""
                        item['city'] = city
                        item['region'] = region
                        item['pais'] = pais
                        yield item
                        
            else:
                for key, value in address_phone_dict.items():
                    
                    item = BancochileClItem()
                    
                    images = {}
                    images['url'] = benefit_logo 
                    images['name'] = nombre_del_comercio
                    item['image_urls'] = images
                    item['nombre_del_beneficio'] = nombre_del_beneficio
                    item['tipo_de_beneficio'] = tipo_de_beneficio
                    item['descripcion_del_beneficio'] = descripcion_del_beneficio
                    item['nombre_del_comercio'] = nombre_del_comercio
                    item['descripcion_del_comercio'] = descripcion_del_comercio
                    item['terminos_y_condiciones_del_beneficio'] = terminos_y_condiciones_del_beneficio
                    item['programa_de_beneficios'] = programa_de_beneficios
                    item['empresa_del_programa'] = empresa_del_programa
                    item['fecha_de_initio'] = fecha_de_initio
                    item['fecha_de_termino'] = fecha_de_termino
                    item['url_beneficio'] = response.url
                    item['categoria'] = response.meta['Categoria']
                    item['web_comercio'] = web_comercio
                    item['telephono_comercio'] = value
                    item['email'] = email
                    item['direccion_comercio'] = key
                    item['county_name'] = ""
                    item['city'] = ""
                    item['region'] = ""
                    item['pais'] = pais
                    yield item
                    
        else:
            item = BancochileClItem()
            
            images = {}
            images['url'] = benefit_logo 
            images['name'] = nombre_del_comercio
            item['image_urls'] = images
            
            item['nombre_del_beneficio'] = nombre_del_beneficio
            item['tipo_de_beneficio'] = tipo_de_beneficio
            item['descripcion_del_beneficio'] = descripcion_del_beneficio
            item['nombre_del_comercio'] = nombre_del_comercio
            item['descripcion_del_comercio'] = descripcion_del_comercio
            item['terminos_y_condiciones_del_beneficio'] = terminos_y_condiciones_del_beneficio
            item['programa_de_beneficios'] = programa_de_beneficios
            item['empresa_del_programa'] = empresa_del_programa
            item['fecha_de_initio'] = fecha_de_initio
            item['fecha_de_termino'] = fecha_de_termino
            item['url_beneficio'] = response.url
            item['categoria'] = response.meta['Categoria']
            item['web_comercio'] = web_comercio
            item['telephono_comercio'] = ""
            item['email'] = ""
            item['direccion_comercio'] = ""
            item['county_name'] = ""
            item['city'] = ""
            item['region'] = ""
            item['pais'] = pais
            yield item

        # Empties the variable, lists, and dict
        city_found = False
        total_cities_found = []
        address_list = []
        my_dict = {}    

        if second_direction_name:    
            # Assigns addresses and strips them of empty spaces
            for i in second_direction_box:
                address = i.xpath('.//text()').extract()
                address = [j.strip() for j in address]
                address_list.append(address)
            # Flattens the nested lists and concatenate the strings in the addresses lists so the phone numbers correspond to their listed address
            joined_list = [' '.join(x) for x in address_list]

            phone_words = ["Teléfono:", "Reservas al fono", "Teléfono", "Reservas:", "Reservas al", "Reservas", "Tel"]
        
            # Creates a dictionary to add the address with it's corresponding number if available
            address_phone_dict = {}
            # Used below to check if a city is matched
            city_match = ""

            # Searches through all the addresses
            for word in phone_words:
                for address in joined_list:
                    if 'www' in address:
                            web_comercio = address
                            joined_list.remove(address)
                    else:
                        if word in address:
                            address_only = address.split(word)[0]
                            phone = address.split(word)[1]
                            joined_list.remove(address)
                            cleaned_phone_number = phone.replace("(", "").replace(")", "").replace("+", "").replace("-","").replace(":", "")
                            if address_only not in address_phone_dict.keys():
                                address_phone_dict[address_only] = cleaned_phone_number
                            
            # Searches through all the addresses
            for address in joined_list:            
                phone_number = ""
                r1 = re.search(phone_regex, address) # Search for a matching regex pattern for a phone number 

                # If a matching regex is found - assigns it as the value to the address key in the address_phone_dict
                # Checks to see if the "Local" keyword exists right before the found number to avoid writing part of the address
                # i.e. Local A200-A202-A204
                # (?<!Local\s)(\(\+\d{4}\)\s\d{3}\s\d{4})
                if r1:
                    phone_number = str(r1.group()) # Assigns phone number
                    start_phone_index = r1.span()[0]
                    end_phone_index = r1.span()[1]
                    
                    # Checks to see if the match is a part of a "Local" address
                    # If found - removes the match and searches again
                    if "Local" in address[start_phone_index - 10: end_phone_index] or "local" in address[start_phone_index - 10: end_phone_index]:
                        string_to_check = address[: start_phone_index] + address[end_phone_index:]
                        r2 = re.search(phone_regex, string_to_check)

                        # If there is a second match without the local part - it should take the phone number
                        if r2:
                            phone_number = str(r2.group())
                            new_address = address.replace(phone_number, "").strip(' .')
                            cleaned_phone_number = phone_number.replace("(", "").replace(")", "").replace("+", "").replace("-","").replace(":", "") # Removes dashes, brackets and plus signs
                            address_phone_dict[new_address] = cleaned_phone_number

                        else:
                            phone_number = ""
                            address_phone_dict[address] = phone_number
                    else:
                        new_address = address.replace(phone_number, "").strip(' .') # Removes the phone number from the whole string and the trailing dot if available
                        cleaned_phone_number = phone_number.replace("(", "").replace(")", "").replace("+", "").replace("-","").replace(":", "") # Removes dashes, brackets and plus signs
                        address_phone_dict[new_address] = cleaned_phone_number
                    
                # If unavailable leaves the phone value empty 
                else:
                    phone_number = "" # Assign an empty phone number field
                    address_phone_dict[address] = phone_number # Add it to the dictionary
                
                # Runs a search with the "Direcciones" string to find a matching city in the chile_communas dictionary
                # If a mathing city is found - gets it's name so a lighter search can be done below
                if process.extractOne(first_direction_name, all_cities, score_cutoff=90): # Tries string matching, score_cutoff=90 is the best match possible
                    total_cities_found.append(process.extractOne(first_direction_name, all_cities, score_cutoff=90)) # Assigns name if match is found 
                """    
                # Checks the length of the total_cities in the list - if only one city is found - sets the city_found boolean to true
                # This is done to assure the list will not be either empty or that it has more than one city to it
                # If it has more than one city - no county, city or region will be output in the csv to avoid presenting wrong information
                """
                if len(total_cities_found) == 1:
                    city_found = True
                    city_match = total_cities_found[0][0] # Assign the matched city to a variable
            if city_found:

                # Gets the Region, City and it's counties
                # If nested dictionary key ( city ) matches the above city's name - assigns it's region, city and it's counties to a new dictionary 
                # which will be used to perform a lighter search below
                for d1, d2 in chile_communas.items(): # Iterate over the dictionary regions and cities
                    for key, value in d2.items(): # Iterates over the nested dictionary ( cities ) and their counties
                        if key == city_match: 
                            region = d1
                            city = key
                            my_dict[d1] = {}
                            my_dict[d1][key] = value

                # Iterates over the new dictionary to get only the counties in a list
                counties = []
                for d1, d2 in my_dict.items():
                    for k, v in d2.items():
                        counties = v

                # Assign a new dictionary for the csv output
                scraped_info = {}

                # Iterates over the address_phone_dict to compare and match counties
                # If a match is found - the county is added to the output, otherwise it's left empty
                for key, value in address_phone_dict.items():
                    item = BancochileClItem()
                    if process.extractOne(key, counties, score_cutoff=90):
                        county_found = process.extractOne(key, counties, score_cutoff=90)
                        county_name = county_found[0]
                        
                        images = {}
                        images['url'] = benefit_logo 
                        images['name'] = nombre_del_comercio
                        item['image_urls'] = images
                        item['nombre_del_beneficio'] = nombre_del_beneficio
                        item['tipo_de_beneficio'] = tipo_de_beneficio
                        item['descripcion_del_beneficio'] = descripcion_del_beneficio
                        item['nombre_del_comercio'] = nombre_del_comercio
                        item['descripcion_del_comercio'] = descripcion_del_comercio
                        item['terminos_y_condiciones_del_beneficio'] = terminos_y_condiciones_del_beneficio
                        item['programa_de_beneficios'] = programa_de_beneficios
                        item['empresa_del_programa'] = empresa_del_programa
                        item['fecha_de_initio'] = fecha_de_initio
                        item['fecha_de_termino'] = fecha_de_termino
                        item['url_beneficio'] = response.url
                        item['categoria'] = response.meta['Categoria']
                        item['web_comercio'] = web_comercio
                        item['telephono_comercio'] = value
                        item['email'] = email
                        item['direccion_comercio'] = key
                        item['county_name'] = county_name
                        item['city'] = city
                        item['region'] = region
                        item['pais'] = pais
                        yield item
                    
                    else:
                        
                        images = {}
                        images['url'] = benefit_logo 
                        images['name'] = nombre_del_comercio
                        item['image_urls'] = images
                        item['nombre_del_beneficio'] = nombre_del_beneficio
                        item['tipo_de_beneficio'] = tipo_de_beneficio
                        item['descripcion_del_beneficio'] = descripcion_del_beneficio
                        item['nombre_del_comercio'] = nombre_del_comercio
                        item['descripcion_del_comercio'] = descripcion_del_comercio
                        item['terminos_y_condiciones_del_beneficio'] = terminos_y_condiciones_del_beneficio
                        item['programa_de_beneficios'] = programa_de_beneficios
                        item['empresa_del_programa'] = empresa_del_programa
                        item['fecha_de_initio'] = fecha_de_initio
                        item['fecha_de_termino'] = fecha_de_termino
                        item['url_beneficio'] = response.url
                        item['categoria'] = response.meta['Categoria']
                        item['web_comercio'] = web_comercio
                        item['telephono_comercio'] = value
                        item['email'] = email
                        item['direccion_comercio'] = key
                        item['county_name'] = ""
                        item['city'] = city
                        item['region'] = region
                        item['pais'] = pais
                        yield item

            else:
                for key, value in address_phone_dict.items():
                    item = BancochileClItem()
                    
                    images = {}
                    images['url'] = benefit_logo 
                    images['name'] = nombre_del_comercio
                    item['image_urls'] = images
                    item['nombre_del_beneficio'] = nombre_del_beneficio
                    item['tipo_de_beneficio'] = tipo_de_beneficio
                    item['descripcion_del_beneficio'] = descripcion_del_beneficio
                    item['nombre_del_comercio'] = nombre_del_comercio
                    item['descripcion_del_comercio'] = descripcion_del_comercio
                    item['terminos_y_condiciones_del_beneficio'] = terminos_y_condiciones_del_beneficio
                    item['programa_de_beneficios'] = programa_de_beneficios
                    item['empresa_del_programa'] = empresa_del_programa
                    item['fecha_de_initio'] = fecha_de_initio
                    item['fecha_de_termino'] = fecha_de_termino
                    item['url_beneficio'] = response.url
                    item['categoria'] = response.meta['Categoria']
                    item['web_comercio'] = web_comercio
                    item['telephono_comercio'] = value
                    item['email'] = email
                    item['direccion_comercio'] = key
                    item['county_name'] = ""
                    item['city'] = ""
                    item['region'] = ""
                    item['pais'] = pais
                    yield item
                
        city_found = False
        total_cities_found = []
        address_list = []
        my_dict = {}