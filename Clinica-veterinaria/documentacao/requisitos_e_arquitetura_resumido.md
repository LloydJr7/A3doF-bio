Documento de requisitos e descrição da arquitetura
==================================================

Sistema de Gestão de Clínica Veterinária – A3

1. Objetivo do projeto

Desenvolver um sistema web para facilitar o gerenciamento de tutores, animais, veterinários, microchips, consultas e vacinas, utilizando integração com o ViaCEP e uma API governamental simulada.

2. Requisitos funcionais

- RF01 – Cadastrar veterinários.
- RF02 – Confirmar senha.
- RF03 – Realizar login e logout de veterinários autorizados.
- RF04 – Gerenciar tutores e validar CPF.
- RF05 – Consultar CEP e gerenciar endereços.
- RF06 – Gerenciar espécies e raças.
- RF07 – Gerenciar animais.
- RF08 – Vincular microchips únicos e manter seu histórico.
- RF09 – Gerenciar consultas.
- RF10 – Consultar histórico clínico.
- RF11 – Registrar vacinas.
- RF12 – Consultar histórico vacinal e próximas doses.
- RF13 – Cadastrar, consultar e atualizar animais na API governamental.
- RF14 – Comunicar vacinações antirrábicas.
- RF15 – Registrar operações de integração.
- RF16 – Permitir reenvio em caso de falhas.
- RF17 – Evitar duplicidade de registros na integração.
- RF18 – Simular respostas, protocolos e falhas governamentais.

3. Requisitos não funcionais

- RNF01 – Interface intuitiva e responsiva.
- RNF02 – Comunicação por API REST, HTTP e JSON.
- RNF03 – Banco de dados relacional e persistência separada entre serviços.
- RNF04 – Validação de dados.
- RNF05 – Autenticação e controle de acesso.
- RNF06 – Proteção de senhas e credenciais.
- RNF07 – Tratamento de erros e indisponibilidade.
- RNF08 – Rastreabilidade das integrações.
- RNF09 – Organização e manutenção do código.
- RNF10 – Documentação das APIs e instruções de execução.
- RNF11 – Utilização de dados fictícios na demonstração.

4. Regras de negócio

- Apenas veterinários ativos e com senha confirmada podem acessar funcionalidades restritas.
- O CPF dos tutores e os códigos dos microchips devem ser únicos.
- Cada animal deve possuir um tutor e uma espécie.
- O peso do animal deve ser positivo.
- Consultas canceladas devem permanecer no histórico.
- Toda vacinação antirrábica deve ser comunicada à API governamental.
- Falhas externas não devem comprometer os registros locais nem gerar duplicidade no reenvio.

5. Arquitetura do sistema

O sistema utiliza uma arquitetura cliente-servidor, dividida nos seguintes componentes:

- Frontend: interface desenvolvida em HTML, CSS e JavaScript.
- Backend: API privada desenvolvida em Python e FastAPI, responsável pelas regras de negócio.
- Banco de dados: PostgreSQL, responsável pelo armazenamento dos dados clínicos.
- ViaCEP: serviço externo para consulta de endereços.
- API governamental: serviço independente para registro de animais e comunicação de vacinas antirrábicas, com persistência própria.

A comunicação entre os serviços ocorre por HTTP e JSON, enquanto o acesso ao PostgreSQL utiliza SQL.

6. Integração governamental

As vacinas antirrábicas devem ser registradas localmente e comunicadas à API governamental. Em caso de falha, a comunicação deve permanecer disponível para reenvio, sem gerar registros duplicados.

7. Segurança e tecnologias

O projeto utiliza Python, FastAPI, PostgreSQL, SQLAlchemy, Pydantic, HTML, CSS e JavaScript. A documentação é realizada pelo Swagger/OpenAPI, os testes pelo Postman e o controle de versão pelo Git e GitHub.

A segurança prevista inclui autenticação por token, proteção de senhas com bcrypt e armazenamento de credenciais em variáveis de ambiente.

8. Pontos de verificação

A implementação de todos os requisitos, a proteção das rotas, a obrigatoriedade dos vínculos, o banco governamental e o funcionamento das integrações devem ser confirmados no código e nos testes.

9. Conclusão

O projeto reúne a gestão de uma clínica veterinária e a integração entre serviços independentes, aplicando conceitos de sistemas distribuídos, segurança, persistência de dados e comunicação entre APIs.
