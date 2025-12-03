# 📅 Dashboard Agenda – Sistema Completo de Gerenciamento de Contatos

Um sistema completo de  **agenda de contatos** , desenvolvido com foco em  **boas práticas** ,  **organização de código** , **testabilidade** e  **padrões profissionais** , ideal para demonstrar habilidades em  **Django** ,  **CRUDs completos** ,  **autenticação** , **templates reutilizáveis** e  **arquitetura limpa** .

Este projeto foi construído como parte do meu desenvolvimento em  **Django** , com objetivo de apresentar domínio real em desenvolvimento backend e frontend integrado no framework.

---

## 🚀 **Tecnologias Utilizadas**

* **Python 3.12+**
* **Django 5+**
* **SQLite (padrão, mas compatível com MySQL/PostgreSQL)**
* **HTML5, CSS3 e Bootstrap 5**
* **Django Templating Engine**
* **Django ORM**
* **Testes automatizados com Django Test Framework**

---

## 🧩 **Principais Funcionalidades**

### ✔️ Autenticação

* Login e logout seguros
* Proteção de rotas
* Sessões do Django

### ✔️ CRUD Completo de Contatos

* Criar, visualizar, editar e excluir contatos
* Upload de imagem do contato
* Campos como nome, email, telefone, descrição e categoria

### ✔️ Dashboard Profissional

* Interface moderna usando Bootstrap
* Layout limpo e responsivo
* Navegação intuitiva

### ✔️ Sistema de Categorias

* Organização dos contatos por categorias personalizadas
* Listagem separada por categoria

### ✔️ Testes Automatizados

* Testes de formulário
* Testes de views
* Testes de autenticação
* Validação de campos obrigatórios

---

## 🏗️ **Arquitetura do Projeto**

O projeto segue uma estrutura simples e organizada:

<pre class="overflow-visible!" data-start="1903" data-end="2297"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>DashboardAgenda/
│
├── agenda/
│   ├── core/               </span><span># Aplicação principal com views, forms e urls</span><span>
│   ├── templates/          </span><span># Templates HTML organizados por telas</span><span>
│   ├── </span><span>static</span><span>/             </span><span># Arquivos estáticos, CSS e imagens</span><span>
│   ├── tests/              </span><span># Testes automatizados</span><span>
│   └── ...
│
├── media/                  </span><span># Uploads dos usuários</span><span>
├── manage.py
└── requirements.txt
</span></span></code></div></div></pre>

Pontos fortes:

* Views organizadas e simplificadas
* Reutilização de templates
* Forms explícitos e validados
* Testes garantindo estabilidade

---

## ⚙️ **Como Rodar o Projeto**

### 1. Clone o repositório

<pre class="overflow-visible!" data-start="2508" data-end="2599"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>git </span><span>clone</span><span> https://github.com/SEU-USUARIO/DashboardAgenda.git
</span><span>cd</span><span> DashboardAgenda
</span></span></code></div></div></pre>

### 2. Crie um ambiente virtual

<pre class="overflow-visible!" data-start="2634" data-end="2735"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>python -m venv venv
</span><span>source</span><span> venv/bin/activate  </span><span># Linux</span><span>
venv\Scripts\activate     </span><span># Windows</span><span>
</span></span></code></div></div></pre>

### 3. Instale as dependências

<pre class="overflow-visible!" data-start="2769" data-end="2812"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>pip install -r requirements.txt
</span></span></code></div></div></pre>

### 4. Realize as migrações

<pre class="overflow-visible!" data-start="2843" data-end="2879"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>python manage.py migrate
</span></span></code></div></div></pre>

### 5. Execute o servidor

<pre class="overflow-visible!" data-start="2908" data-end="2946"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>python manage.py runserver
</span></span></code></div></div></pre>

Acesse em:

👉 **[http://127.0.0.1:8000]()**

---

## 🧪 **Como executar os testes**

<pre class="overflow-visible!" data-start="3031" data-end="3064"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>python manage.py </span><span>test</span><span>
</span></span></code></div></div></pre>

---

## 📸 **Screenshots**

![1764721394571](image/README/1764721394571.png)

![1764721193899](image/README/1764721193899.png)

![1764721230327](image/README/1764721230327.png)

![1764721286340](image/README/1764721286340.png)

![1764721314798](image/README/1764721314798.png)

![1764721339308](image/README/1764721339308.png)

---

## 🎯 **Objetivo deste Projeto**

Este projeto foi desenvolvido como parte do meu processo de evolução em  **Desenvolvimento Web** , aplicando:

* Django na prática
* Boas práticas de arquitetura
* Testes profissionais
* Padrões de desenvolvimento usados no mercado

Ele tem como foco demonstrar minhas habilidades como **desenvolvedor backend** e minha capacidade de criar aplicações completas com organização, segurança e escalabilidade.

---

## 📌 **Possíveis Melhorias Futuras**

* Paginação de contatos
* Filtros avançados por categoria, nome e data
* API REST com Django Rest Framework
* Exportação de contatos (Excel/PDF)
* Painel administrativo customizado

---

## 👤 **Autor**

**Felipe Rocha**

Desenvolvedor Backend / Full Stack em formação

Apaixonado por tecnologia, qualidade e boas práticas no desenvolvimento de software.
