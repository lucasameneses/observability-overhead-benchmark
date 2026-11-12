-- TrainTicket benchmark schema (adapted)
-- Database: shared PostgreSQL instance for ts-order-service, ts-payment-service, ts-travel-service

-- ============================================
-- ts-order-service database
-- ============================================

CREATE DATABASE tsorder;
\c tsorder;

CREATE TABLE orders (
    id              VARCHAR(36) PRIMARY KEY,
    bought_date     VARCHAR(20),
    travel_date     VARCHAR(20),
    travel_time     VARCHAR(20),
    account_id      VARCHAR(36),
    contacts_name   VARCHAR(100),
    document_type   INTEGER DEFAULT 0,
    train_number    VARCHAR(20),
    coach_number    INTEGER DEFAULT 1,
    seat_class      INTEGER DEFAULT 3,
    seat_number     VARCHAR(10),
    from_station    VARCHAR(100),
    to_station      VARCHAR(100),
    status          INTEGER DEFAULT 0,
    price           VARCHAR(20)
);

INSERT INTO orders (id, bought_date, travel_date, travel_time, account_id, contacts_name, document_type, train_number, coach_number, seat_class, seat_number, from_station, to_station, status, price) VALUES
('ord-001', '2025-01-15', '2025-02-01', '08:00', 'acc-001', 'Carlos Silva', 0, 'G1', 1, 3, '1A', 'Fortaleza', 'Sao Paulo', 1, '185.50'),
('ord-002', '2025-01-16', '2025-02-02', '10:30', 'acc-002', 'Maria Santos', 0, 'G2', 2, 2, '3B', 'Sao Paulo', 'Rio de Janeiro', 1, '120.00'),
('ord-003', '2025-01-17', '2025-02-03', '14:00', 'acc-003', 'Joao Oliveira', 1, 'G3', 3, 1, '5C', 'Rio de Janeiro', 'Belo Horizonte', 0, '95.00'),
('ord-004', '2025-01-18', '2025-02-04', '16:45', 'acc-001', 'Ana Costa', 0, 'G4', 1, 3, '2D', 'Belo Horizonte', 'Salvador', 0, '210.00'),
('ord-005', '2025-01-19', '2025-02-05', '07:30', 'acc-004', 'Pedro Lima', 0, 'G1', 2, 2, '4A', 'Fortaleza', 'Recife', 1, '75.00');

-- ============================================
-- ts-payment-service database
-- ============================================

CREATE DATABASE tspayment;
\c tspayment;

CREATE TABLE payments (
    id              VARCHAR(36) PRIMARY KEY,
    order_id        VARCHAR(36),
    user_id         VARCHAR(36),
    payment_price   VARCHAR(20)
);

INSERT INTO payments (id, order_id, user_id, payment_price) VALUES
('pay-001', 'ord-001', 'acc-001', '185.50'),
('pay-002', 'ord-002', 'acc-002', '120.00'),
('pay-003', 'ord-005', 'acc-004', '75.00');

-- ============================================
-- ts-travel-service database
-- ============================================

CREATE DATABASE tstravel;
\c tstravel;

CREATE TABLE trips (
    trip_id                 VARCHAR(36),
    train_type_name          VARCHAR(50),
    route_id                 VARCHAR(36),
    start_station_name       VARCHAR(100),
    stations_name            VARCHAR(500),
    terminal_station_name    VARCHAR(100),
    start_time               VARCHAR(10),
    end_time                 VARCHAR(10),
    PRIMARY KEY (trip_id, train_type_name)
);

INSERT INTO trips (trip_id, train_type_name, route_id, start_station_name, stations_name, terminal_station_name, start_time, end_time) VALUES
('G1', 'HighSpeed', 'route-001', 'Fortaleza', 'Fortaleza,Recife,Salvador', 'Sao Paulo', '08:00', '18:00'),
('G2', 'Express', 'route-002', 'Sao Paulo', 'Sao Paulo,Rio de Janeiro', 'Rio de Janeiro', '10:30', '13:00'),
('G3', 'Regional', 'route-003', 'Rio de Janeiro', 'Rio de Janeiro,Belo Horizonte', 'Belo Horizonte', '14:00', '17:30'),
('G4', 'HighSpeed', 'route-004', 'Belo Horizonte', 'Belo Horizonte,Vitoria,Salvador', 'Salvador', '16:45', '22:00'),
('G5', 'Express', 'route-005', 'Fortaleza', 'Fortaleza,Recife', 'Recife', '07:30', '10:00');