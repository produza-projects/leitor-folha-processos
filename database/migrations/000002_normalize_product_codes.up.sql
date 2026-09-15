-- Refuse ambiguous or invalid cleanup instead of changing data silently.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM caminhos
        WHERE btrim(cod_produto) !~ '^[0-9]{4}[.][0-9]{6}$'
    ) THEN
        RAISE EXCEPTION
            'caminhos.cod_produto contains values outside the expected format';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM caminhos
        GROUP BY btrim(cod_produto)
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION
            'caminhos.cod_produto contains duplicates after trimming';
    END IF;
END
$$;

UPDATE caminhos
SET cod_produto = btrim(cod_produto)
WHERE cod_produto <> btrim(cod_produto);

ALTER TABLE caminhos
    ADD CONSTRAINT caminhos_cod_produto_formato_check
    CHECK (cod_produto ~ '^[0-9]{4}[.][0-9]{6}$');
