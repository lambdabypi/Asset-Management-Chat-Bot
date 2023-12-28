use assets;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255)
);

select * from assets;
select * from people;

DELETE FROM assets
LIMIT 10000;
DELETE FROM people
LIMIT 10000;