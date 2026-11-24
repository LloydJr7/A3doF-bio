CREATE TABLE IF NOT EXISTS public.endereco (
	id serial4 NOT NULL,
	cep varchar(9) NOT NULL,
	logradouro varchar(150) NOT NULL,
	numero varchar(20) NOT NULL,
	complemento varchar(50) NULL,
	bairro varchar(100) NOT NULL,
	cidade varchar(100) NOT NULL,
	uf varchar(2) NOT NULL,
	codigo_ibge varchar(10) NULL,
	CONSTRAINT endereco_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.veterinario (
	id serial4 NOT NULL,
	nome_completo varchar(150) NOT NULL,
	cpf varchar(14) NOT NULL,
	crmv varchar(20) NOT NULL,
	uf_crmv varchar(2) NOT NULL,
	email varchar(100) NOT NULL,
	telefone varchar(20) NULL,
	senha_hash varchar(255) NOT NULL,
	senha_confirmada bool DEFAULT false NULL,
	data_confirmacao timestamp NULL,
	situacao varchar(10) DEFAULT 'ATIVO'::character varying NULL,
	data_cadastro timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	ultimo_acesso timestamp NULL,
	CONSTRAINT veterinario_cpf_key UNIQUE (cpf),
	CONSTRAINT veterinario_email_key UNIQUE (email),
	CONSTRAINT veterinario_pkey PRIMARY KEY (id),
	CONSTRAINT veterinario_situacao_check CHECK (((situacao)::text = ANY ((ARRAY['ATIVO'::character varying, 'INATIVO'::character varying])::text[])))
);

CREATE TABLE IF NOT EXISTS public.tutor (
	id serial4 NOT NULL,
	nome_completo varchar(150) NOT NULL,
	cpf varchar(14) NOT NULL,
	data_nascimento date NOT NULL,
	email varchar(100) NOT NULL,
	telefone varchar(20) NOT NULL,
	endereco_id int4 NULL,
	situacao varchar(10) DEFAULT 'ATIVO'::character varying NULL,
	data_cadastro timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT tutor_cpf_key UNIQUE (cpf),
	CONSTRAINT tutor_pkey PRIMARY KEY (id),
	CONSTRAINT tutor_situacao_check CHECK (((situacao)::text = ANY ((ARRAY['ATIVO'::character varying, 'INATIVO'::character varying])::text[]))),
	CONSTRAINT tutor_endereco_id_fkey FOREIGN KEY (endereco_id) REFERENCES public.endereco(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.especies (
	id serial4 NOT NULL,
	nome varchar(100) NOT NULL,
	descricao text NULL,
	ativo bool DEFAULT true NULL,
	CONSTRAINT especies_nome_key UNIQUE (nome),
	CONSTRAINT especies_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.racas (
	id serial4 NOT NULL,
	nome varchar(100) NOT NULL,
	descricao text NULL,
	especie_id int4 NOT NULL,
	ativo bool DEFAULT true NULL,
	CONSTRAINT racas_pkey PRIMARY KEY (id),
	CONSTRAINT uq_raca_especie UNIQUE (nome, especie_id),
	CONSTRAINT fk_raca_especie FOREIGN KEY (especie_id) REFERENCES public.especies(id)
);

CREATE TABLE IF NOT EXISTS public.animais (
	id serial4 NOT NULL,
	nome varchar(100) NOT NULL,
	data_nascimento date NULL,
	idade_estimada int4 NULL,
	sexo varchar(10) NULL,
	cor varchar(100) NULL,
	peso_atual numeric(6, 2) NULL,
	tutor_id int4 NULL,
	especie_id int4 NOT NULL,
	raca_id int4 NULL,
	ativo bool DEFAULT true NULL,
	CONSTRAINT animais_pkey PRIMARY KEY (id),
	CONSTRAINT chk_animal_idade CHECK ((idade_estimada >= 0)),
	CONSTRAINT chk_animal_peso CHECK ((peso_atual > (0)::numeric)),
	CONSTRAINT chk_animal_sexo CHECK (((sexo)::text = ANY ((ARRAY['Macho'::character varying, 'Femea'::character varying])::text[]))),
	CONSTRAINT fk_animais_tutor FOREIGN KEY (tutor_id) REFERENCES public.tutor(id),
	CONSTRAINT fk_animal_especie FOREIGN KEY (especie_id) REFERENCES public.especies(id),
	CONSTRAINT fk_animal_raca FOREIGN KEY (raca_id) REFERENCES public.racas(id)
);

CREATE TABLE IF NOT EXISTS public.microchips (
	id serial4 NOT NULL,
	animal_id int4 NOT NULL,
	codigo varchar(50) NOT NULL,
	data_implantacao date NULL,
	observacoes text NULL,
	ativo bool DEFAULT true NOT NULL,
	CONSTRAINT microchips_animal_id_key UNIQUE (animal_id),
	CONSTRAINT microchips_codigo_key UNIQUE (codigo),
	CONSTRAINT microchips_pkey PRIMARY KEY (id),
	CONSTRAINT fk_microchip_animal FOREIGN KEY (animal_id) REFERENCES public.animais(id)
);

CREATE TABLE IF NOT EXISTS public.consultas (
	id serial4 NOT NULL,
	animal_id int4 NOT NULL,
	veterinario_id int4 NULL,
	data_hora timestamp NOT NULL,
	motivo text NULL,
	status varchar(20) DEFAULT 'agendada'::character varying NOT NULL,
	observacoes text NULL,
	ativo bool DEFAULT true NOT NULL,
	CONSTRAINT ck_consulta_status CHECK (((status)::text = ANY ((ARRAY['agendada'::character varying, 'realizada'::character varying, 'cancelada'::character varying])::text[]))),
	CONSTRAINT consultas_pkey PRIMARY KEY (id),
	CONSTRAINT fk_consulta_animal FOREIGN KEY (animal_id) REFERENCES public.animais(id)
);

CREATE TABLE IF NOT EXISTS public.vacina (
	id serial4 NOT NULL,
	animal_id int4 NOT NULL,
	veterinario_id int4 NOT NULL,
	nome varchar(120) NOT NULL,
	antirrabica bool DEFAULT false NOT NULL,
	fabricante varchar(120) NULL,
	lote varchar(80) NOT NULL,
	dose varchar(40) NOT NULL,
	data_aplicacao date NOT NULL,
	data_proxima_dose date NULL,
	observacoes text NULL,
	data_cadastro timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT vacina_pkey PRIMARY KEY (id),
	CONSTRAINT fk_vacina_animal FOREIGN KEY (animal_id) REFERENCES public.animais(id),
	CONSTRAINT fk_vacina_veterinario FOREIGN KEY (veterinario_id) REFERENCES public.veterinario(id),
	CONSTRAINT ck_vacina_proxima_dose CHECK (data_proxima_dose IS NULL OR data_proxima_dose >= data_aplicacao)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_vacina_registro
	ON public.vacina (animal_id, lower(nome), data_aplicacao, upper(lote), lower(dose));

CREATE TABLE IF NOT EXISTS public.integracao_governo (
	id serial4 NOT NULL,
	vacina_id int4 NOT NULL,
	status varchar(20) DEFAULT 'pendente' NOT NULL,
	tentativas int4 DEFAULT 0 NOT NULL,
	protocolo varchar(120) NULL,
	ultimo_erro text NULL,
	data_ultima_tentativa timestamp NULL,
	data_envio timestamp NULL,
	data_atualizacao timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT integracao_governo_pkey PRIMARY KEY (id),
	CONSTRAINT uq_integracao_governo_vacina UNIQUE (vacina_id),
	CONSTRAINT fk_integracao_governo_vacina FOREIGN KEY (vacina_id) REFERENCES public.vacina(id),
	CONSTRAINT ck_integracao_governo_status CHECK (status IN ('pendente', 'enviando', 'erro', 'enviado')),
	CONSTRAINT ck_integracao_governo_tentativas CHECK (tentativas >= 0)
);

INSERT INTO public.especies (id, nome, descricao, ativo) VALUES
(1, 'Cachorro', 'Canino', true),
(2, 'Gato', 'Felino', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.racas (id, nome, descricao, especie_id, ativo) VALUES
(1, 'SRD (Vira-lata)', 'Sem raça definida', 1, true),
(2, 'Labrador', 'Labrador Retriever', 1, true),
(3, 'Poodle', 'Poodle', 1, true),
(4, 'SRD (Vira-lata)', 'Sem raça definida', 2, true),
(5, 'Siamês', 'Gato Siamês', 2, true),
(6, 'Persa', 'Gato Persa', 2, true)
ON CONFLICT (id) DO NOTHING;