from django.shortcuts import render
from bs4 import BeautifulSoup
import requests

def get_content(product, site, country):
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
    LANGUAGE = "en-US,en;q=0.5"
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    
    base_urls = {
        'jumia': {
            'ng': f'https://www.jumia.com.ng/catalog/?q={product}',
            'ke': f'https://www.jumia.co.ke/catalog/?q={product}',
            # Add more countries for Jumia as needed
        },
        'amazon': {
            'us': f'https://www.amazon.com/s?k={product}',
            'uk': f'https://www.amazon.co.uk/s?k={product}',
            # Add more countries for Amazon as needed
        },
        'jiji': {
            'ng': f'https://www.jiji.ng/search?query={product}',
            # Add more countries for Jiji as needed
        }
    }

    url = base_urls.get(site, {}).get(country)
    
    if not url:
        return None

    response = session.get(url)
    if response.status_code != 200:
        return None

    return response.text

def parse_jumia(soup):
    product_info_list = []
    product_items = soup.find_all('article', class_='prd _fb col c-prd')
    
    for item in product_items:
        name_tag = item.find('h3', class_='name')
        price_tag = item.find('div', class_='prc')
        img_c_div = item.find('div', class_='img-c')
        img_tag = img_c_div.find('img', class_='img') if img_c_div else None
        stars_div = item.find('div', class_='stars _s')
        rating_div = stars_div.find('div', class_='in') if stars_div else None

        if name_tag and price_tag and img_tag and rating_div:
            name = name_tag.text.strip()
            price = price_tag.text.strip()
            img_url = img_tag.get('data-src', '') if img_tag else ''

            style_attribute = rating_div.get('style', '')
            width_value = style_attribute.split(':')[1].replace('%', '').strip()
            rating = f'{float(width_value) / 20:.1f}'
            
            product_info = {
                'name': name,
                'price': price,
                'image_url': img_url,
                'rating': rating
            }
            
            product_info_list.append(product_info)
    
    return product_info_list

def parse_amazon(soup):
    product_info_list = []
    product_items = soup.find_all('div', class_='a-section')

    for item in product_items:
        name_tag = item.find('span', class_='a-size-medium a-color-base a-text-normal')
        price_whole = item.find('span', class_='a-price-fraction')
        price_fraction = item.find('span', class_='a-price-fraction')
        img_tag = item.find('img', class_='s-image')
        rating_tag = item.find('span', class_='a-icon-alt')

        if name_tag and price_whole and img_tag and rating_tag:
            name = name_tag.text.strip()
            price = f"${price_whole.text.strip()}.{price_fraction.text.strip() if price_fraction else '00'}"
            img_url = img_tag.get('src', '')
            rating = rating_tag.text.split(' ')[0].strip()
            
            product_info = {
                'name': name,
                'price': price,
                'image_url': img_url,
                'rating': rating
            }
            
            product_info_list.append(product_info)
    
    return product_info_list

def parse_jiji(soup):
    product_info_list = []
    product_items = soup.find_all('div', class_='b-list-advert__item')

    for item in product_items:
        name_tag = item.find('a', class_='b-list-advert__item-title')
        price_tag = item.find('div', class_='b-list-advert__item-price')
        img_tag = item.find('img', class_='b-list-advert__item-img')
        rating_tag = item.find('div', class_='b-star-rating__star')

        if name_tag and price_tag and img_tag:
            name = name_tag.text.strip()
            price = price_tag.text.strip()
            img_url = img_tag.get('src', '')
            rating = rating_tag.get('aria-label', '0').split(' ')[0] if rating_tag else '0'
            
            product_info = {
                'name': name,
                'price': price,
                'image_url': img_url,
                'rating': rating
            }
            
            product_info_list.append(product_info)
    
    return product_info_list

def home(request):
    product_info_list = []

    if 'product' in request.GET:
        product = request.GET.get('product')
        country = request.GET.get('country', 'ng')  # Default to Nigeria if no country is selected

        # Scrape Jumia
        html_content_jumia = get_content(product, 'jumia', country)
        if html_content_jumia:
            soup_jumia = BeautifulSoup(html_content_jumia, 'html.parser')
            product_info_list.extend(parse_jumia(soup_jumia))
        
        # Scrape Amazon
        html_content_amazon = get_content(product, 'amazon', country)
        if html_content_amazon:
            soup_amazon = BeautifulSoup(html_content_amazon, 'html.parser')
            product_info_list.extend(parse_amazon(soup_amazon))
        
        # Scrape Jiji
        html_content_jiji = get_content(product, 'jiji', country)
        if html_content_jiji:
            soup_jiji = BeautifulSoup(html_content_jiji, 'html.parser')
            product_info_list.extend(parse_jiji(soup_jiji))

    return render(request, 'core/home.html', {'product_info_list': product_info_list})
