from pytubefix import YouTube
import os
import subprocess
import argparse
import shutil
import sys


def sanitize_title(title: str) -> str:
    """Cria um nome de arquivo seguro para Windows."""
    return "".join(c for c in title if c.isalnum() or c in (" ", ".", "_", "-")).strip()


def stream_extension(stream) -> str:
    """Obtém a extensão do stream a partir do mime_type (fallback para mp4)."""
    try:
        if stream.mime_type:
            return stream.mime_type.split("/")[-1]
    except Exception:
        pass
    return "mp4"


def _resolve_ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.getcwd()
    local = os.path.join(base, exe)
    if os.path.exists(local):
        return local
    return None

def ffmpeg_merge(video_filename: str, audio_filename: str, output_filename: str, hide_console: bool = False):
    ffmpeg_bin = _resolve_ffmpeg()
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg não encontrado. Instale e adicione ao PATH ou coloque ffmpeg.exe ao lado do executável.")
    command = [
        ffmpeg_bin,
        "-y",
        "-i",
        video_filename,
        "-i",
        audio_filename,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-strict",
        "experimental",
        output_filename,
    ]
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" and hide_console else 0
    subprocess.run(command, check=True, creationflags=creationflags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ffmpeg_extract_audio(input_filename: str, audio_out_filename: str, hide_console: bool = False):
    ffmpeg_bin = _resolve_ffmpeg()
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg não encontrado. Instale e adicione ao PATH ou coloque ffmpeg.exe ao lado do executável.")
    command = [
        ffmpeg_bin,
        "-y",
        "-i",
        input_filename,
        "-vn",
        "-c:a",
        "aac",
        audio_out_filename,
    ]
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" and hide_console else 0
    subprocess.run(command, check=True, creationflags=creationflags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def baixar_video_youtube(url, modo_auto: bool = False, listar_apenas: bool = False, resolucao_especifica: str | None = None, saida_dir: str | None = None):
    """
    Baixa o vídeo do YouTube a partir da URL fornecida, permitindo a escolha da resolução
    e lidando com streams adaptativos (separados).
    """
    try:
        yt = YouTube(url)
        print(f"Título do vídeo: {yt.title}\n")
        base_title = sanitize_title(yt.title)
        out_dir = saida_dir or os.getcwd()

        print("Listando todos os streams disponíveis:")
        # Use os filtros nativos do pytubefix para garantir listagem correta
        progressive_streams = (
            yt.streams.filter(progressive=True).order_by("resolution").desc()
        )
        video_only_streams = (
            yt.streams.filter(only_video=True).order_by("resolution").desc()
        )
        audio_only_streams = (
            yt.streams.filter(only_audio=True).order_by("abr").desc()
        )

        # Exibir streams progressivos
        if progressive_streams:
            print("\n--- STREAMS PROGRESSIVOS (Vídeo + Áudio) ---")
            for i, stream in enumerate(progressive_streams):
                print(
                    f"P{i+1}. ITAG: {stream.itag} | Res: {stream.resolution} | Fps: {stream.fps} | Formato: {stream_extension(stream)}"
                )
        else:
            print("\nNenhum stream progressivo disponível (vídeo + áudio).")

        # Exibir streams de vídeo (sem áudio)
        if video_only_streams:
            print("\n--- STREAMS DE VÍDEO (Sem Áudio) ---")
            for i, stream in enumerate(video_only_streams):
                print(
                    f"V{i+1}. ITAG: {stream.itag} | Res: {stream.resolution} | Fps: {stream.fps} | Formato: {stream_extension(stream)}"
                )
        else:
            print("\nNenhum stream de vídeo (sem áudio) disponível.")

        # Exibir streams de áudio
        if audio_only_streams:
            print("\n--- STREAMS DE ÁUDIO (Apenas Áudio) ---")
            for i, stream in enumerate(audio_only_streams):
                print(
                    f"A{i+1}. ITAG: {stream.itag} | Bitrate: {stream.abr} | Formato: {stream_extension(stream)}"
                )
        else:
            print("\nNenhum stream de áudio disponível.")

        print(
            "\nPara baixar vídeos em alta resolução (ex: 1080p), você geralmente precisará baixar"
        )
        print(
            "um 'STREAM DE VÍDEO (Sem Áudio)' e um 'STREAM DE ÁUDIO' separadamente, e depois combiná-los com FFmpeg."
        )

        # Se for apenas para listar formatos, não segue para interação
        if listar_apenas:
            return

        # Se o usuário pediu uma resolução específica, tentar baixar essa
        if resolucao_especifica:
            target_video = None
            for s in video_only_streams:
                if s.resolution == resolucao_especifica:
                    target_video = s
                    break
            if target_video:
                vext = stream_extension(target_video)
                video_filename = f"{base_title}_video_temp.{vext}"
                print(
                    f"\nBaixando vídeo {resolucao_especifica}: (ITAG: {target_video.itag})..."
                )
                target_video.download(output_path=out_dir, filename=video_filename)

                # pegar melhor áudio
                target_audio = audio_only_streams.first()
                if target_audio:
                    aext = stream_extension(target_audio)
                    audio_filename = f"{base_title}_audio_temp.{aext}"
                    print(
                        f"Baixando áudio: {target_audio.abr} (ITAG: {target_audio.itag})..."
                    )
                    target_audio.download(output_path=out_dir, filename=audio_filename)
                else:
                    # Fallback: extrai áudio do melhor progressivo
                    best_prog = progressive_streams.first()
                    if best_prog:
                        prog_ext = stream_extension(best_prog)
                        prog_filename = f"{base_title}_prog_temp.{prog_ext}"
                        print(
                            f"Nenhum áudio separado encontrado. Baixando progressivo {best_prog.resolution} para extrair áudio..."
                        )
                        best_prog.download(output_path=out_dir, filename=prog_filename)
                        audio_filename = f"{base_title}_audio_temp.aac"
                        print("Extraindo áudio do progressivo com FFmpeg...")
                        ffmpeg_extract_audio(os.path.join(out_dir, prog_filename), os.path.join(out_dir, audio_filename))
                        try:
                            os.remove(os.path.join(out_dir, prog_filename))
                        except OSError:
                            pass
                    else:
                        print("Não foi possível obter áudio para combinar.")
                        return

                print("\nCombinando vídeo e áudio com FFmpeg...")
                output_filename = os.path.join(out_dir, f"{base_title}_final.mp4")
                try:
                    ffmpeg_merge(os.path.join(out_dir, video_filename), os.path.join(out_dir, audio_filename), output_filename)
                    print(f"Vídeo final combinado: '{output_filename}'")
                except subprocess.CalledProcessError as e:
                    print(f"Erro ao combinar com FFmpeg: {e}")
                finally:
                    try:
                        os.remove(os.path.join(out_dir, video_filename))
                        os.remove(os.path.join(out_dir, audio_filename))
                    except OSError:
                        pass
                return
            else:
                print(
                    f"Não foi encontrado stream de vídeo com resolução {resolucao_especifica}."
                )
                # Continua para modo automático/interativo

        # Modo automático: tenta baixar o melhor progressivo, caso contrário combina melhor vídeo+áudio
        if modo_auto:
            try:
                best_progressive = (
                    yt.streams.filter(progressive=True, file_extension="mp4")
                    .order_by("resolution")
                    .desc()
                    .first()
                )
                if best_progressive:
                    ext = stream_extension(best_progressive)
                    filename = f"{base_title}_progressivo.{ext}"
                    print(
                        f"\nBaixando automaticamente: {best_progressive.resolution} (ITAG: {best_progressive.itag})..."
                    )
                    best_progressive.download(output_path=out_dir, filename=filename)
                    print("Download concluído com sucesso!")
                    return

                # Caso não exista progressivo bom, baixa melhor vídeo e melhor áudio
                best_video = (
                    yt.streams.filter(only_video=True)
                    .order_by("resolution")
                    .desc()
                    .first()
                )
                best_audio = (
                    yt.streams.filter(only_audio=True)
                    .order_by("abr")
                    .desc()
                    .first()
                )

                if best_video:
                    vext = stream_extension(best_video)
                    video_filename = f"{base_title}_video_temp.{vext}"
                    print(
                        f"\nBaixando vídeo: {best_video.resolution} (ITAG: {best_video.itag})..."
                    )
                    best_video.download(output_path=out_dir, filename=video_filename)
                else:
                    print("Não foi possível encontrar um stream de vídeo adequado.")
                    return

                if best_audio:
                    aext = stream_extension(best_audio)
                    audio_filename = f"{base_title}_audio_temp.{aext}"
                    print(
                        f"Baixando áudio: {best_audio.abr} (ITAG: {best_audio.itag})..."
                    )
                    best_audio.download(output_path=out_dir, filename=audio_filename)
                else:
                    print("Não foi possível encontrar um stream de áudio adequado.")
                    return

                print("\nCombinando vídeo e áudio com FFmpeg...")
                output_filename = os.path.join(out_dir, f"{base_title}_final.mp4")
                try:
                    ffmpeg_merge(os.path.join(out_dir, video_filename), os.path.join(out_dir, audio_filename), output_filename)
                    print(f"Vídeo final combinado: '{output_filename}'")
                except subprocess.CalledProcessError as e:
                    print(f"Erro ao combinar com FFmpeg: {e}")
                    print(
                        "Certifique-se de que o FFmpeg está instalado e configurado no seu PATH."
                    )
                    print(
                        f"Você pode precisar combinar os arquivos manualmente usando: ffmpeg -i \"{os.path.join(out_dir, video_filename)}\" -i \"{os.path.join(out_dir, audio_filename)}\" -c:v copy -c:a aac \"{output_filename}\""
                    )

                try:
                    os.remove(video_filename)
                    os.remove(audio_filename)
                    print("Arquivos temporários removidos.")
                except OSError as e:
                    print(f"Erro ao remover arquivos temporários: {e}")
                return
            except Exception as e:
                print(f"Erro no modo automático: {e}")
                # Se falhar, continua para modo interativo

        while True:
            escolha_tipo = input("\nEscolha o tipo de download (P para progressivo, V para vídeo, A para áudio, S para sair): ").lower()

            if escolha_tipo == 's':
                print("Download cancelado.")
                return

            if escolha_tipo == 'p' and progressive_streams:
                while True:
                    escolha_stream = input("Digite o número do stream progressivo (ex: P1): ").lower()
                    try:
                        index = int(escolha_stream[1:]) - 1
                        if 0 <= index < len(progressive_streams):
                            stream_selecionado = progressive_streams[index]
                            print(f"\nBaixando stream progressivo: {stream_selecionado.resolution} (ITAG: {stream_selecionado.itag})...")
                            pext = stream_extension(stream_selecionado)
                            filename = f"{base_title}_progressivo.{pext}"
                            stream_selecionado.download(output_path=out_dir, filename=filename)
                            print("Download concluído com sucesso!")
                            return
                        else:
                            print("Número inválido. Por favor, digite um número da lista.")
                    except (ValueError, IndexError):
                        print("Entrada inválida. Por favor, digite no formato P<número>.")
            elif escolha_tipo == 'v' and video_only_streams:
                while True:
                    escolha_stream_video = input("Digite o número do STREAM DE VÍDEO (ex: V1): ").lower()
                    try:
                        index_video = int(escolha_stream_video[1:]) - 1
                        if 0 <= index_video < len(video_only_streams):
                            video_stream_selecionado = video_only_streams[index_video]
                            print(f"\nBaixando stream de vídeo: {video_stream_selecionado.resolution} (ITAG: {video_stream_selecionado.itag})...")
                            # Sanitize filename for common OS issues and ensure unique temp names
                            vext = stream_extension(video_stream_selecionado)
                            video_filename = f"{base_title}_video_temp.{vext}"
                            video_stream_selecionado.download(output_path=out_dir, filename=video_filename)
                            print("Download do vídeo concluído!")

                            # Agora, pede para escolher o áudio
                            if audio_only_streams:
                                while True:
                                    escolha_stream_audio = input("Digite o número do STREAM DE ÁUDIO para combinar (ex: A1): ").lower()
                                    try:
                                        index_audio = int(escolha_stream_audio[1:]) - 1
                                        if 0 <= index_audio < len(audio_only_streams):
                                            audio_stream_selecionado = audio_only_streams[index_audio]
                                            print(f"\nBaixando stream de áudio: {audio_stream_selecionado.abr} (ITAG: {audio_stream_selecionado.itag})...")
                                            aext = stream_extension(audio_stream_selecionado)
                                            audio_filename = f"{base_title}_audio_temp.{aext}"
                                            audio_stream_selecionado.download(output_path=out_dir, filename=audio_filename)
                                            print("Download do áudio concluído!")

                                            print("\nCombinando vídeo e áudio com FFmpeg...")
                                            output_filename = os.path.join(out_dir, f"{base_title}_final.mp4")
                                            # Comando FFmpeg para combinar vídeo e áudio
                                            # -y para sobrescrever se o arquivo existir
                                            try:
                                                ffmpeg_merge(os.path.join(out_dir, video_filename), os.path.join(out_dir, audio_filename), output_filename)
                                                print(f"Vídeo final combinado: '{output_filename}'")
                                            except subprocess.CalledProcessError as e:
                                                print(f"Erro ao combinar com FFmpeg: {e}")
                                                print("Certifique-se de que o FFmpeg está instalado e configurado no seu PATH.")
                                                print("Você pode precisar combinar os arquivos manualmente usando:")
                                                print(f"ffmpeg -i \"{video_filename}\" -i \"{audio_filename}\" -c:v copy -c:a aac \"{output_filename}\"")


                                            # Opcional: remover arquivos temporários
                                            try:
                                                os.remove(os.path.join(out_dir, video_filename))
                                                os.remove(os.path.join(out_dir, audio_filename))
                                                print("Arquivos temporários removidos.")
                                            except OSError as e:
                                                print(f"Erro ao remover arquivos temporários: {e}")
                                            return
                                        else:
                                            print("Número inválido para áudio. Por favor, digite um número da lista.")
                                    except (ValueError, IndexError):
                                        print("Entrada inválida. Por favor, digite no formato A<número>.")
                            else:
                                print("Nenhum stream de áudio disponível para combinar. Baixado apenas o vídeo.")
                                return
                        else:
                            print("Número inválido para vídeo. Por favor, digite um número da lista.")
                    except (ValueError, IndexError):
                        print("Entrada inválida. Por favor, digite no formato V<número>.")
            elif escolha_tipo == 'a' and audio_only_streams:
                while True:
                    escolha_stream = input("Digite o número do stream de áudio (ex: A1): ").lower()
                    try:
                        index = int(escolha_stream[1:]) - 1
                        if 0 <= index < len(audio_only_streams):
                            stream_selecionado = audio_only_streams[index]
                            print(f"\nBaixando stream de áudio: {stream_selecionado.abr} (ITAG: {stream_selecionado.itag})...")
                            aext = stream_extension(stream_selecionado)
                            filename = f"{base_title}_audio_only.{aext}"
                            stream_selecionado.download(output_path=out_dir, filename=filename)
                            print("Download do áudio concluído!")
                            return
                        else:
                            print("Número inválido. Por favor, digite um número da lista.")
                    except (ValueError, IndexError):
                        print("Entrada inválida. Por favor, digite no formato A<número>.")
            else:
                print("Escolha inválida ou tipo de stream não disponível. Tente novamente.")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Downloader de YouTube com escolha de resolução e pós-processamento via FFmpeg")
    parser.add_argument("--url", help="URL do vídeo do YouTube")
    parser.add_argument("--auto", action="store_true", help="Modo automático: baixa melhor opção disponível e combina se necessário")
    parser.add_argument("--list", action="store_true", help="Apenas listar formatos disponíveis e sair")
    parser.add_argument("--res", help="Forçar download em resolução específica (ex.: 1080p, 720p)")
    parser.add_argument("--outdir", help="Diretório de saída para salvar os arquivos")
    args = parser.parse_args()

    if not args.url:
        url_do_video = input("Por favor, insira a URL do vídeo do YouTube que você quer baixar: ")
    else:
        url_do_video = args.url

    baixar_video_youtube(url_do_video, modo_auto=args.auto, listar_apenas=args.list, resolucao_especifica=args.res, saida_dir=args.outdir)