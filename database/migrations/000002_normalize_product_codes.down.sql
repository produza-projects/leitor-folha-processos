ALTER TABLE caminhos
    DROP CONSTRAINT IF EXISTS caminhos_cod_produto_formato_check;

-- The removed whitespace is intentionally not restored: it was invalid data,
-- not part of the product code.
