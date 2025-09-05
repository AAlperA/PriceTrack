# PriceTrack

This project is all about scraping markets, saving data to MySQL and provide access through a Django Rest Framework (DRF) based REST API. The project uses Docker for containerization and RabbitMQ for inter-service messaging.

## Features

- REST API (Django + Django REST Framework)

- JWT-based authentication (login / refresh / protected endpoints; API access only)

- Django Admin panel (accessible with superuser) for managing data and exploring the API through its web interface

- Docker for local development

- Data exchange between services using RabbitMQ message queues

- Each scraper, storage, API, database, and message broker runs in its own container

- Scrapers that pull product information using site's own API, Playwright & BeautifulSoup

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.<br><br>

## SETUP

### Prerequisites

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) & [Docker Compose](https://docs.docker.com/compose/install/) (recommended)

2. [Python 3.13+](https://www.python.org/downloads/windows/)

3. Virtualenv

4. Install dependencies:

    ```bash 
    pip install -r requirements.txt
    ``` 

5. Create your own `.env` file based on `.env.example`

6. Make sure to set the directories in the yml files to your own directory

7. Optional for API usage: [Postman](https://www.postman.com/)

### Build & Start Project With Docker Compose

```bash
docker-compose mysql-docker.yml  up -d --build
docker-compose rabbitmq-docker.yml  up -d --build
docker-compose api-docker.yml  up -d --build
.
.
.
```
## How To Use

### Registration

1.  Via Django superuser account using the Admin panel (full access through web interface)

2. Via JWT authentication

### Local Hosts 
- RabbitMQ interface: http://localhost:15672/#/
- Register API: http://localhost:8000/api/register/
- Login API: http://localhost:8000/api/login/
- List all products: http://localhost:8000/api/products/ 
- List all prices: http://localhost:8000/api/prices/ 
- List both products and prices: http://localhost:8000/api/whole/ 
- Admin interface: http://localhost:8000/admin/ 

### Filtering via URL 

You can filter the results with query. Some examples: 

- /api/products/?market=a101 
- /api/products/?brand=Nestle&product_name=Chocolate 
- /api/whole/?market=migros&campaign=Discount 
- /api/prices/?product_id=10&special_price=50 

#### Allowed Query Parameters 
products: 

    market, 
    brand, 
    product_name, 
    product_id, 
    product_image 

prices: 

    product_id, 
    price_id, 
    special_price, 
    regular_price, 
    price_date, 
    campaign 

whole: 

    market, 
    brand, 
    product_name, 
    product_id, 

## Demo / Showcase
Below are some gifs taken to illustrate the project in action:

### Storage log
![Storage_log](https://github.com/user-attachments/assets/222b0489-3c03-46bc-a7f0-c1e9e77e7dc0)

### API Register-Login-Response
![API_request](https://github.com/user-attachments/assets/25412db4-37af-4d16-8960-cc3480473518)

### API Admin Usage
![API_admin](https://github.com/user-attachments/assets/4927ff70-176f-4f4c-9151-53add6aaba5e)

