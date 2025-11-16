import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import platform
import sys

from pytubefix import YouTube
from YouTubeDonwloader import (
    ffmpeg_merge,
    ffmpeg_extract_audio,
    stream_extension,
    sanitize_title,
)


class QueueItem:
    def __init__(self, url, title, res, audio_lang, out_dir):
        self.url = url
        self.title = title
        self.res = res
        self.audio_lang = audio_lang
        self.out_dir = out_dir
        self.progress = 0
        self.status = "Na fila"
        self.format = "MP4"
        self.thread = None


class DownloaderGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("900x600")
        try:
            base = getattr(sys, "_MEIPASS", os.getcwd())
            icon_path = os.path.join(base, "assets", "video_download.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        # Variáveis
        self.url_var = tk.StringVar()
        self.res_var = tk.StringVar(value="Automático")
        self.audio_var = tk.StringVar(value="Automático")
        self.status_var = tk.StringVar(value="Pronto.")
        self.out_dir = os.getcwd()

        self.queue_items = []  # até 10 itens
        self.item_widgets = []  # widgets por linha

        # Estilos para tabela zebrada
        self.style = ttk.Style()
        self.style.configure("ZebraEven.TFrame", background="#f7f7f7")
        self.style.configure("ZebraOdd.TFrame", background="#ffffff")
        self.style.configure("ZebraEven.TLabel", background="#f7f7f7")
        self.style.configure("ZebraOdd.TLabel", background="#ffffff")

        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Seção superior - URL e opções
        url_frame = ttk.LabelFrame(main_frame, text="Configurações de Download", padding=10)
        url_frame.pack(fill="x", pady=(0, 10))

        # URL do vídeo
        ttk.Label(url_frame, text="Cole a URL do vídeo aqui:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=80)
        url_entry.grid(row=1, column=0, columnspan=4, sticky="we", pady=(0, 10))
        url_entry.focus()

        # Resolução - Radio buttons
        ttk.Label(url_frame, text="Escolha a resolução:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        res_frame = ttk.Frame(url_frame)
        res_frame.grid(row=3, column=0, sticky="w", pady=(0, 10))
        
        ttk.Radiobutton(res_frame, text="Automático", variable=self.res_var, value="Automático").pack(side="left", padx=(0, 15))
        ttk.Radiobutton(res_frame, text="1080p", variable=self.res_var, value="1080p").pack(side="left", padx=(0, 15))
        ttk.Radiobutton(res_frame, text="720p", variable=self.res_var, value="720p").pack(side="left", padx=(0, 15))
        ttk.Radiobutton(res_frame, text="480p", variable=self.res_var, value="480p").pack(side="left")

        # Faixa de áudio - Combobox
        ttk.Label(url_frame, text="Escolha a faixa de áudio:").grid(row=2, column=2, sticky="w", padx=(20, 0), pady=(0, 5))
        audio_combo = ttk.Combobox(url_frame, textvariable=self.audio_var, values=["Automático", "Inglês", "Português"], state="readonly", width=15)
        audio_combo.grid(row=3, column=2, sticky="w", padx=(20, 0), pady=(0, 10))

        # Pasta de destino
        dest_frame = ttk.Frame(url_frame)
        dest_frame.grid(row=4, column=0, columnspan=4, sticky="we", pady=(0, 10))
        
        ttk.Button(dest_frame, text="Selecionar pasta de destino", command=self.choose_folder).pack(side="left")
        self.out_label = ttk.Label(dest_frame, text=self.out_dir, foreground="#555")
        self.out_label.pack(side="left", padx=(10, 0))

        # Botão Iniciar Download
        download_btn = ttk.Button(url_frame, text="Iniciar Download", command=self.start_download)
        download_btn.grid(row=5, column=0, columnspan=4, pady=(10, 0))

        url_frame.columnconfigure(0, weight=1)

        # Separador
        ttk.Separator(main_frame).pack(fill="x", pady=10)

        # Tabela de downloads
        table_frame = ttk.LabelFrame(main_frame, text="Fila de Downloads", padding=10)
        table_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Cabeçalho da tabela
        header = ttk.Frame(table_frame)
        header.pack(fill="x", pady=(0, 5))
        
        ttk.Label(header, text="Vídeo", width=35, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Resolução", width=12, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Local", width=25, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=2, sticky="w")
        ttk.Label(header, text="Progresso", width=15, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=3, sticky="w")
        ttk.Label(header, text="Ações", width=20, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=4, sticky="w")

        # Frame scrollável para a fila
        canvas = tk.Canvas(table_frame, height=200)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        self.queue_frame = ttk.Frame(canvas)

        self.queue_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.queue_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")
        
        # Rodapé com versão
        version_label = ttk.Label(status_frame, text="YouTube Downloader | v0.02", foreground="#888")
        version_label.pack(side="right")

    def choose_folder(self):
        path = filedialog.askdirectory(initialdir=self.out_dir)
        if path:
            self.out_dir = path
            self.out_label.config(text=self.out_dir)

    def start_download(self):
        if len(self.queue_items) >= 10:
            messagebox.showwarning("Limite", "A fila suporta no máximo 10 itens.")
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Atenção", "Informe a URL do vídeo.")
            return

        res = self.res_var.get()
        audio_lang = self.audio_var.get()

        try:
            yt = YouTube(url)
            title = sanitize_title(yt.title)
        except Exception:
            title = "(Sem título)"

        item = QueueItem(url, title, res, audio_lang, self.out_dir)
        self.queue_items.append(item)
        
        # Limpa o campo de URL
        self.url_var.set("")
        
        self._render_queue()
        self._start_item_download(item)

    def _render_queue(self):
        # Limpa widgets existentes
        for widget_set in self.item_widgets:
            for widget in widget_set:
                if hasattr(widget, 'destroy'):
                    widget.destroy()
        self.item_widgets = []

        # Renderiza cada item da fila
        for idx, item in enumerate(self.queue_items):
            row_style = "ZebraEven.TFrame" if idx % 2 == 0 else "ZebraOdd.TFrame"
            label_style = "ZebraEven.TLabel" if idx % 2 == 0 else "ZebraOdd.TLabel"
            
            row = ttk.Frame(self.queue_frame, style=row_style)
            row.pack(fill="x", pady=2)

            # Título do vídeo
            title_label = ttk.Label(row, text=item.title[:45] + "..." if len(item.title) > 45 else item.title, 
                                  style=label_style, width=35)
            title_label.grid(row=0, column=0, sticky="w", padx=(5, 0))

            # Resolução
            res_label = ttk.Label(row, text=item.res, style=label_style, width=12)
            res_label.grid(row=0, column=1, sticky="w")

            # Local (pasta)
            local_text = os.path.basename(item.out_dir) if item.out_dir else "N/A"
            local_label = ttk.Label(row, text=local_text, style=label_style, width=25)
            local_label.grid(row=0, column=2, sticky="w")

            # Barra de progresso
            progress_bar = ttk.Progressbar(row, length=120, mode="determinate")
            progress_bar.grid(row=0, column=3, sticky="w", padx=(5, 0))
            progress_bar["value"] = item.progress

            # Botões de ação
            action_frame = ttk.Frame(row)
            action_frame.grid(row=0, column=4, sticky="w", padx=(5, 0))

            open_btn = ttk.Button(action_frame, text="Abrir local", width=10,
                                command=lambda i=item: self.open_location(i))
            open_btn.pack(side="left", padx=(0, 5))

            cancel_btn = ttk.Button(action_frame, text="Cancelar", width=8,
                                  command=lambda i=item: self.cancel_download(i))
            cancel_btn.pack(side="left")

            # Armazena widgets para atualização posterior
            self.item_widgets.append((row, title_label, res_label, local_label, progress_bar, open_btn, cancel_btn))

    def open_location(self, item: QueueItem):
        """Abre a pasta onde o arquivo foi salvo"""
        if os.path.exists(item.out_dir):
            if platform.system() == "Windows":
                os.startfile(item.out_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", item.out_dir])
            else:  # Linux
                subprocess.run(["xdg-open", item.out_dir])
        else:
            messagebox.showwarning("Aviso", "Pasta não encontrada.")

    def cancel_download(self, item: QueueItem):
        """Cancela o download e remove da fila"""
        try:
            if item in self.queue_items:
                # Para a thread se estiver rodando
                if hasattr(item, 'thread') and item.thread and item.thread.is_alive():
                    # Não há como parar thread de forma segura, apenas marca como cancelado
                    item.status = "Cancelado"
                
                self.queue_items.remove(item)
                self._render_queue()
                self.status_var.set(f"Download cancelado: {item.title}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cancelar download: {e}")

    def _update_progress_widget(self, idx, value):
        """Atualiza a barra de progresso de um item específico"""
        if idx < len(self.item_widgets):
            progress_bar = self.item_widgets[idx][4]
            progress_bar["value"] = max(0, min(100, value))

    def _start_item_download(self, item: QueueItem):
        """Inicia o download em thread separada"""
        def run():
            try:
                self._download_item(item)
                item.status = "Concluído"
                item.progress = 100
                idx = self.queue_items.index(item) if item in self.queue_items else -1
                if idx >= 0:
                    self.root.after(0, lambda: self._update_progress_widget(idx, item.progress))
                    self.root.after(0, lambda: self.status_var.set(f"Concluído: {item.title}"))
            except Exception as e:
                item.status = f"Erro: {e}"
                self.root.after(0, lambda: self.status_var.set(f"Erro: {e}"))

        item.thread = threading.Thread(target=run, daemon=True)
        item.thread.start()

    def _download_item(self, item: QueueItem):
        """Executa o download do item"""
        # Preparação
        yt = YouTube(item.url, on_progress_callback=lambda s, c, br: self._on_stream_progress(item, s, br))

        # Escolha de streams baseada na resolução
        if item.res == "Automático":
            # Tenta progressivo primeiro
            prog = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
            if prog:
                ext = stream_extension(prog)
                filename = f"{item.title}_final.{ext}"
                self.root.after(0, lambda: self.status_var.set(f"Baixando: {item.title} ({prog.resolution})"))
                prog.download(output_path=item.out_dir, filename=filename)
                item.progress = 100
                idx = self.queue_items.index(item) if item in self.queue_items else -1
                if idx >= 0:
                    self.root.after(0, lambda: self._update_progress_widget(idx, item.progress))
                return
            # Sem progressivo: baixa melhor vídeo + melhor áudio
            v_stream = yt.streams.filter(only_video=True).order_by("resolution").desc().first()
        else:
            # Busca resolução específica
            v_stream = None
            for s in yt.streams.filter(only_video=True).order_by("resolution").desc():
                if s.resolution == item.res:
                    v_stream = s
                    break

        if not v_stream:
            raise RuntimeError(f"Stream de vídeo não encontrado para a resolução {item.res}.")

        # Seleção de áudio baseada na preferência
        a_stream = None
        if item.audio_lang == "Inglês":
            # Tenta encontrar áudio em inglês (isso é uma simplificação)
            a_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        elif item.audio_lang == "Português":
            # Tenta encontrar áudio em português (isso é uma simplificação)
            a_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        else:  # Automático
            a_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()

        # Baixar vídeo
        vext = stream_extension(v_stream)
        video_filename = f"{item.title}_video_temp.{vext}"
        self.root.after(0, lambda: self.status_var.set(f"Baixando vídeo: {item.title} ({v_stream.resolution})"))
        item.progress = 0
        idx = self.queue_items.index(item) if item in self.queue_items else -1
        if idx >= 0:
            self.root.after(0, lambda: self._update_progress_widget(idx, item.progress))
        v_stream.download(output_path=item.out_dir, filename=video_filename)
        item.progress = 50
        if idx >= 0:
            self.root.after(0, lambda: self._update_progress_widget(idx, item.progress))

        # Baixar áudio (ou fallback)
        if a_stream:
            aext = stream_extension(a_stream)
            audio_filename = f"{item.title}_audio_temp.{aext}"
            self.root.after(0, lambda: self.status_var.set(f"Baixando áudio: {item.title} ({a_stream.abr})"))
            a_stream.download(output_path=item.out_dir, filename=audio_filename)
        else:
            # Fallback: extrai áudio de progressivo
            prog = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
            if not prog:
                raise RuntimeError("Áudio não disponível e não foi possível baixar progressivo para extração.")
            prog_ext = stream_extension(prog)
            prog_filename = f"{item.title}_prog_temp.{prog_ext}"
            self.root.after(0, lambda: self.status_var.set(f"Baixando progressivo para extrair áudio: {item.title}"))
            prog.download(output_path=item.out_dir, filename=prog_filename)
            audio_filename = f"{item.title}_audio_temp.aac"
            ffmpeg_extract_audio(
                os.path.join(item.out_dir, prog_filename),
                os.path.join(item.out_dir, audio_filename),
                hide_console=True,
            )
            try:
                os.remove(os.path.join(item.out_dir, prog_filename))
            except OSError:
                pass

        item.progress = 80
        if idx >= 0:
            self.root.after(0, lambda: self._update_progress_widget(idx, item.progress))

        # Merge final
        self.root.after(0, lambda: self.status_var.set(f"Mesclando: {item.title}"))
        output_filename = os.path.join(item.out_dir, f"{item.title}_final.mp4")
        ffmpeg_merge(
            os.path.join(item.out_dir, video_filename),
            os.path.join(item.out_dir, audio_filename),
            output_filename,
            hide_console=True,
        )
        
        # Limpeza de arquivos temporários
        try:
            os.remove(os.path.join(item.out_dir, video_filename))
            os.remove(os.path.join(item.out_dir, audio_filename))
        except OSError:
            pass

        item.progress = 100
        if idx >= 0:
            self.root.after(0, lambda: self._update_progress_widget(idx, item.progress))

    def _on_stream_progress(self, item: QueueItem, stream, bytes_remaining):
        """Callback de progresso do pytubefix"""
        try:
            total = getattr(stream, "filesize", None) or getattr(stream, "filesize_approx", None)
            if total:
                downloaded = max(0, total - bytes_remaining)
                # Progresso unificado: vídeo até 50%, áudio até 80%, merge até 100%
                if stream.is_adaptive or (stream.includes_video_track and not stream.includes_audio_track):
                    pct = (downloaded / total) * 50.0
                elif stream.includes_audio_track and not stream.includes_video_track:
                    pct = 50.0 + (downloaded / total) * 30.0
                else:
                    pct = (downloaded / total) * 80.0
                
                item.progress = min(80.0, pct)
                idx = self.queue_items.index(item) if item in self.queue_items else -1
                if idx >= 0:
                    self.root.after(0, lambda: self._update_progress_widget(idx, item.progress))
        except Exception:
            pass


def main():
    root = tk.Tk()
    app = DownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()