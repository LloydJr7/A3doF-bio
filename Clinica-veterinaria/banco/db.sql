create table endereco (
	id SERIAL primary key,
	cep VARCHAR(9) not null,
	logradouro VARCHAR(150) not null,
	numero VARCHAR(20) not null,
	complemento VARCHAR(50),
	bairro VARCHAR(100) not null,
	cidade VARCHAR(100) not null,
	uf VARCHAR(2) not null,
	codigo_ibge VARCHAR(10)
);

create table veterinario (
	id SERIAL primary key,
	nome_completo VARCHAR(150) not null,
	cpf VARCHAR(14) unique not null,
	crmv VARCHAR(20) not null,
	uf_crmv VARCHAR(2) not null,
	email VARCHAR(100) unique not null,
	telefone VARCHAR(20),
	senha_hash VARCHAR(255) not null,
	senha_confirmada BOOLEAN default false,
	data_confirmacao TIMESTAMP,
	situacao VARCHAR(10) check (situacao in ('ATIVO', 'INATIVO')) default 'ATIVO',
	data_cadastro TIMESTAMP default current_TIMESTAMP,
	ultimo_acesso TIMESTAMP 
	);

create table tutor (
	id SERIAL primary key,
	nome_completo VARCHAR(150) not null,
	cpf VARCHAR(14) unique not null,
	data_nascimento DATE not null,
	email VARCHAR(100) not null,
	telefone VARCHAR(20) not null,
	endereco_id INT references endereco(id) on delete set null,
	situacao VARCHAR(10) check (situacao in ('ATIVO', 'INATIVO')) default 'ATIVO',
	data_cadastro TIMESTAMP default current_timestamp
	);