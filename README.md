🏗️ Estimador de Obras - MVP

Este projeto é um protótipo de um aplicativo de estimativa de custos para construção civil, desenvolvido para demonstrar a criação de ferramentas úteis de forma rápida e eficiente usando o ecossistema Python. A versão atual (MVP) está focada em fornecer uma ferramenta precisa para o cálculo de materiais e custos de reboco de parede.

Como Funciona

O aplicativo web permite que o usuário insira as dimensões de uma parede (comprimento, altura) e as especificações dos materiais (espessura do reboco, rendimento e preço do cimento). Com base nesses dados, ele executa os seguintes cálculos:

    Área e Volume: Determina a área e o volume total do reboco.

    Materiais: Estima a quantidade de sacos de cimento e o volume de areia necessários.

    Custos: Calcula o custo dos materiais e da mão de obra para fornecer uma estimativa de custo total.

Funcionalidades Principais

    Interface Intuitiva: Criada com Streamlit, oferece uma experiência de usuário simples e direta.

    Salvamento em Nuvem: As estimativas podem ser salvas e recuperadas de um banco de dados Google Firestore, garantindo que nenhum dado seja perdido.

    Exportação em PDF: Gere e baixe relatórios profissionais em PDF com todos os detalhes da estimativa, prontos para serem compartilhados.

Tecnologias Utilizadas

    Streamlit: Para a interface de usuário e a lógica do aplicativo web.

    Firebase Admin SDK (Firestore): Para a persistência de dados e o gerenciamento do histórico de estimativas.

    ReportLab: Para a geração dinâmica dos relatórios em PDF.


https://lordkrc-orcamento-venvapp-ijqond.streamlit.app/
