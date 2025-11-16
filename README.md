# YouTube Downloader

Aplicativo simples para baixar conteúdo do YouTube de forma prática no Windows. Focado em uso direto por usuários finais sem necessidade de instalar dependências.

## O que é

- Ferramenta de desktop para baixar vídeos do YouTube
- Interface direta: cole a URL, escolha o formato e baixe
- Funciona sem instalação (apenas um arquivo `.exe`)

## Apenas Executável (Importante)

- Este projeto é distribuído para usuários finais na forma de um único executável.
- Você só precisa do arquivo `YouTubeDownloader.exe` para usar o aplicativo.
- Não é necessário compilar, instalar bibliotecas ou configurar ambiente.

## Como Usar

1. Baixe o arquivo `YouTubeDownloader.exe`.
2. Dê duplo clique para abrir.
3. Cole a URL do vídeo do YouTube.
4. Selecione o formato desejado (por exemplo, vídeo ou áudio).
5. Clique em “Baixar” e aguarde a conclusão.

## Requisitos

- Windows 10 ou superior
- Conexão com a internet

## FFmpeg (necessário para 1080p e mesclagem áudio/vídeo)

- O aplicativo usa `ffmpeg` para combinar vídeo e áudio quando o YouTube fornece faixas separadas (comum em 1080p).
- Se o `ffmpeg` não estiver disponível, você verá erros como `WinError 2` ou mensagens de "FFmpeg não encontrado".

### Opção A — Instalar FFmpeg no sistema (recomendado)

- Baixe um build estável do FFmpeg para Windows e extraia.
- Coloque `ffmpeg.exe` em uma pasta fixa, por exemplo `C:\ffmpeg\bin`.
- Adicione essa pasta ao `PATH` do Windows:
  - Abra "Variáveis de Ambiente" → edite `PATH` do usuário → adicione `C:\ffmpeg\bin` → OK.
- Verifique no terminal:
  - `ffmpeg -version`

### Opção B — Colocar ao lado do executável

- Copie `ffmpeg.exe` para a mesma pasta do `YouTubeDownloader.exe`.
- Abra o `.exe` normalmente. O app detecta `ffmpeg.exe` no mesmo diretório.

### Quando é exigido

- Necessário para resoluções como `1080p` (vídeo sem áudio) e para conversão/extração de áudio.
- Em alguns downloads "progressivos" (vídeo+áudio juntos), o `ffmpeg` pode não ser usado, mas mantenha instalado para garantir compatibilidade.

### Erros comuns

- `Erro: [WinError 2] O sistema não pode encontrar o arquivo especificado` → instale o FFmpeg ou coloque `ffmpeg.exe` ao lado do `.exe`.
- `FFmpeg não encontrado` → confirme `ffmpeg -version` no terminal ou a presença de `ffmpeg.exe` junto ao executável.

## Dicas e Segurança

- Se o Windows mostrar o SmartScreen, escolha “Mais informações” → “Executar assim mesmo”.
- Somente baixe o `.exe` de fontes confiáveis fornecidas pelo mantenedor do projeto.

## Atualizações

- Para atualizar, substitua o seu `YouTubeDownloader.exe` pela versão mais recente e abra normalmente.
