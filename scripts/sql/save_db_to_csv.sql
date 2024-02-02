copy (select {columns}
from {table_name} {where_clause}) TO '{absolute_path}' DELIMITER ',' CSV HEADER;
