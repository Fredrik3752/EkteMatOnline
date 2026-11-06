-- Ekte Mat Online – SQLite schema (temporary store, replaced by Neo4j in oblig 5)
-- Prices are stored as integer øre (100 øre = 1 NOK).

DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS guest_groups;
DROP TABLE IF EXISTS order_lines;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS food_item_dietary_labels;
DROP TABLE IF EXISTS food_item_allergens;
DROP TABLE IF EXISTS food_item_categories;
DROP TABLE IF EXISTS food_items;
DROP TABLE IF EXISTS dietary_labels;
DROP TABLE IF EXISTS allergens;
DROP TABLE IF EXISTS event_categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    phone         TEXT,
    role          TEXT    NOT NULL DEFAULT 'customer'
                          CHECK (role IN ('customer', 'admin')),
    created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE event_categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT    NOT NULL UNIQUE,
    name       TEXT    NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE allergens (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT    NOT NULL UNIQUE,
    name TEXT    NOT NULL
);

CREATE TABLE dietary_labels (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT    NOT NULL UNIQUE,
    name TEXT    NOT NULL
);

CREATE TABLE food_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    description   TEXT    NOT NULL DEFAULT '',
    price_ore     INTEGER NOT NULL CHECK (price_ore >= 0),
    min_order_qty INTEGER NOT NULL DEFAULT 1 CHECK (min_order_qty >= 1),
    image_path    TEXT,
    origin        TEXT,
    is_published  INTEGER NOT NULL DEFAULT 0 CHECK (is_published IN (0, 1)),
    created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE food_item_categories (
    food_item_id      INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    event_category_id INTEGER NOT NULL REFERENCES event_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (food_item_id, event_category_id)
);

CREATE TABLE food_item_allergens (
    food_item_id INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    allergen_id  INTEGER NOT NULL REFERENCES allergens(id) ON DELETE CASCADE,
    PRIMARY KEY (food_item_id, allergen_id)
);

CREATE TABLE food_item_dietary_labels (
    food_item_id     INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    dietary_label_id INTEGER NOT NULL REFERENCES dietary_labels(id) ON DELETE CASCADE,
    PRIMARY KEY (food_item_id, dietary_label_id)
);

CREATE TABLE orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id         INTEGER NOT NULL REFERENCES users(id),
    event_date          TEXT    NOT NULL,              -- ISO date YYYY-MM-DD
    guest_count         INTEGER NOT NULL CHECK (guest_count >= 1),
    delivery_address    TEXT    NOT NULL,
    notes               TEXT    NOT NULL DEFAULT '',
    status              TEXT    NOT NULL DEFAULT 'submitted'
                        CHECK (status IN ('submitted', 'approved', 'in_preparation',
                                          'delivered', 'rejected', 'cancelled')),
    payment_status      TEXT    NOT NULL DEFAULT 'not_paid'
                        CHECK (payment_status IN ('not_paid', 'deposit_paid', 'invoiced', 'paid')),
    estimated_total_ore INTEGER NOT NULL DEFAULT 0 CHECK (estimated_total_ore >= 0),
    created_at          TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_orders_status     ON orders(status);
CREATE INDEX idx_orders_event_date ON orders(event_date);
CREATE INDEX idx_orders_customer   ON orders(customer_id);

-- Name and unit price are copied at order time, so later menu edits
-- do not change existing orders.
CREATE TABLE order_lines (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id       INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    food_item_id   INTEGER REFERENCES food_items(id) ON DELETE SET NULL,
    item_name      TEXT    NOT NULL,
    quantity       INTEGER NOT NULL CHECK (quantity >= 1),
    unit_price_ore INTEGER NOT NULL CHECK (unit_price_ore >= 0)
);

-- Allergies and diets per guest group, not per named guest (GDPR art. 9).
CREATE TABLE guest_groups (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    description   TEXT    NOT NULL,
    guest_count   INTEGER NOT NULL CHECK (guest_count >= 1),
    allergy_notes TEXT    NOT NULL DEFAULT '',
    dietary_notes TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE questions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    author_id   INTEGER NOT NULL REFERENCES users(id),
    body        TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    answer      TEXT,
    answered_by INTEGER REFERENCES users(id),
    answered_at TEXT
);

-- Reference data -------------------------------------------------------------

INSERT INTO event_categories (slug, name, sort_order) VALUES
    ('birthday',          'Bursdag',          10),
    ('confirmation',      'Konfirmasjon',     20),
    ('wedding',           'Bryllup',          30),
    ('conference',        'Konferanse og møte', 40),
    ('christmas-party',   'Julebord',         50),
    ('corporate-lunch',   'Firmalunsj',       60),
    ('memorial',          'Minnesamvær',      70);

-- The 14 allergens that must be declared under EU/Norwegian food labelling rules.
INSERT INTO allergens (code, name) VALUES
    ('gluten',      'Gluten'),
    ('crustaceans', 'Skalldyr'),
    ('eggs',        'Egg'),
    ('fish',        'Fisk'),
    ('peanuts',     'Peanøtter'),
    ('soy',         'Soya'),
    ('milk',        'Melk'),
    ('nuts',        'Nøtter'),
    ('celery',      'Selleri'),
    ('mustard',     'Sennep'),
    ('sesame',      'Sesam'),
    ('sulphites',   'Sulfitt'),
    ('lupin',       'Lupin'),
    ('molluscs',    'Bløtdyr');

INSERT INTO dietary_labels (code, name) VALUES
    ('vegetarian',   'Vegetar'),
    ('vegan',        'Vegansk'),
    ('gluten-free',  'Glutenfri'),
    ('lactose-free', 'Laktosefri'),
    ('halal',        'Halal');
