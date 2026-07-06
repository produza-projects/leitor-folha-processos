-- ============================================================
-- Tabela: caminhos
-- Armazena o caminho associado a cada código de produto.
-- ============================================================
CREATE TABLE caminhos (
    -- Identificador interno da tabela.
    -- Gerado automaticamente pelo PostgreSQL.
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Código único do produto.
    -- Utilizado para localizar o caminho correspondente.
    cod_produto TEXT NOT NULL UNIQUE,

    -- Caminho armazenado em formato de texto.
    caminho TEXT
);

-- ============================================================
-- Tabela: ordens_fabricacao
-- Relaciona uma ordem de fabricação ao caminho utilizado.
-- ============================================================
CREATE TABLE ordens_fabricacao (
    -- Número da Ordem de Fabricação (OF).
    -- Código de negócio fornecido pelo ERP.
    -- Atualmente possui 7 dígitos (ex.: 2619006).
    ordem_fabricacao INT PRIMARY KEY,

    -- Referência ao registro da tabela "caminhos".
    caminho_id BIGINT NOT NULL,

    -- Impede que um caminho seja removido caso esteja
    -- associado a alguma ordem de fabricação.
    CONSTRAINT fk_caminho
        FOREIGN KEY (caminho_id)
        REFERENCES caminhos(id)
        ON DELETE RESTRICT
);

-- ============================================================
-- Índice da chave estrangeira.
-- O PostgreSQL cria índices automaticamente apenas para
-- PRIMARY KEY e UNIQUE. Para FOREIGN KEY é recomendável
-- criar manualmente, melhorando JOINs, consultas por
-- caminho_id e verificações de integridade referencial.
-- ============================================================
CREATE INDEX idx_ordens_fabricacao_caminho_id
    ON ordens_fabricacao(caminho_id);