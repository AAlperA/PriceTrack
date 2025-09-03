DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    brand VARCHAR(255),
    market VARCHAR(40) NOT NULL,
    product_image VARCHAR(255),
    tags JSON DEFAULT ('{}'),
    UNIQUE (product_name, market)
)
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE prices (
    price_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    special_price DECIMAL(10,2),
    regular_price DECIMAL(10,2) NOT NULL,
    price_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    campaign VARCHAR(255),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
)
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

