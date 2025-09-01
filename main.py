import customtkinter as ctk
from tkinter import filedialog, messagebox
from pypdf import PdfWriter
import os
import threading

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Configuração da Janela Principal ---
        self.title("Compilador de PDFs")
        self.geometry("800x600")
        ctk.set_appearance_mode("Dark")  # Opções: "Dark", "Light", "System"
        ctk.set_default_color_theme("blue")

        self.pdf_files = []
        self.is_merging = False

        # --- Layout Principal (Grid) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Título ---
        self.title_label = ctk.CTkLabel(self, text="Compilador de PDFs", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # --- Frame Principal (Lista de Arquivos e Área de Drop) ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # --- Frame com Rolagem para a Lista de PDFs ---
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Use o botão '➕ Adicionar' para incluir seus PDFs")
        self.scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # --- Frame para os Botões de Ação ---
        self.buttons_frame = ctk.CTkFrame(self)
        self.buttons_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.add_button = ctk.CTkButton(self.buttons_frame, text="➕ Adicionar PDFs", command=self.add_files)
        self.add_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.clear_button = ctk.CTkButton(self.buttons_frame, text="🗑️ Limpar Lista", command=self.clear_list, fg_color="#D32F2F", hover_color="#B71C1C")
        self.clear_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.merge_button = ctk.CTkButton(self.buttons_frame, text="💾 Compilar e Salvar", command=self.merge_and_save, state="disabled")
        self.merge_button.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        
        # --- Barra de Status ---
        self.status_label = ctk.CTkLabel(self, text="Pronto. Adicione 2 ou mais arquivos para mesclar.", anchor="w")
        self.status_label.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Armazena a cor padrão do texto para resetar de forma segura mais tarde
        self.default_status_text_color = self.status_label.cget("text_color")

    def add_files(self):
        """Abre o diálogo para selecionar arquivos PDF."""
        files = filedialog.askopenfilenames(
            title="Selecione os arquivos PDF",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if files:
            self.pdf_files.extend(files)
            self.update_file_list_ui()
            self.status_label.configure(text=f"{len(files)} arquivo(s) adicionado(s).")

    def update_file_list_ui(self):
        """Atualiza a interface da lista de arquivos."""
        # Limpa os widgets antigos
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Atualiza o texto do label do frame
        if not self.pdf_files:
            self.scrollable_frame.configure(label_text="Use o botão 'Adicionar' para incluir seus PDFs")
        else:
            self.scrollable_frame.configure(label_text="Arquivos para Mesclar")

        # Adiciona os novos widgets da lista
        for i, file_path in enumerate(self.pdf_files):
            file_frame = ctk.CTkFrame(self.scrollable_frame)
            file_frame.pack(fill="x", padx=5, pady=5)
            file_frame.grid_columnconfigure(0, weight=1)

            filename = os.path.basename(file_path)
            label = ctk.CTkLabel(file_frame, text=f"{i+1}. {filename}", anchor="w")
            label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

            # --- Botões de Reordenar e Deletar ---
            button_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
            button_frame.grid(row=0, column=1, padx=5, pady=5)

            up_button = ctk.CTkButton(button_frame, text="↑", width=30, command=lambda index=i: self.move_file(index, -1))
            up_button.pack(side="left", padx=(0, 5))
            if i == 0:
                up_button.configure(state="disabled")

            down_button = ctk.CTkButton(button_frame, text="↓", width=30, command=lambda index=i: self.move_file(index, 1))
            down_button.pack(side="left", padx=(0, 5))
            if i == len(self.pdf_files) - 1:
                down_button.configure(state="disabled")

            delete_button = ctk.CTkButton(button_frame, text="✕", width=30, fg_color="#D32F2F", hover_color="#B71C1C", command=lambda index=i: self.remove_file(index))
            delete_button.pack(side="left")

        # Atualiza o estado do botão de mesclar
        self.merge_button.configure(state="normal" if len(self.pdf_files) >= 2 else "disabled")

    def move_file(self, index, direction):
        """Move um arquivo para cima ou para baixo na lista."""
        if self.is_merging: return
        
        new_index = index + direction
        if 0 <= new_index < len(self.pdf_files):
            self.pdf_files.insert(new_index, self.pdf_files.pop(index))
            self.update_file_list_ui()

    def remove_file(self, index):
        """Remove um arquivo da lista."""
        if self.is_merging: return
        
        self.pdf_files.pop(index)
        self.update_file_list_ui()
        self.status_label.configure(text="Arquivo removido.")

    def clear_list(self):
        """Limpa todos os arquivos da lista."""
        if self.is_merging: return
        
        if self.pdf_files and messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar a lista de arquivos?"):
            self.pdf_files.clear()
            self.update_file_list_ui()
            self.status_label.configure(text="Lista de arquivos limpa.")

    def merge_and_save(self):
        """Inicia o processo de mesclagem e salvamento."""
        if self.is_merging: return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
            title="Salvar PDF Mesclado Como..."
        )

        if not save_path:
            self.status_label.configure(text="Operação de salvamento cancelada.")
            return

        # Desabilita a UI e atualiza o status ANTES de iniciar a thread
        self.is_merging = True
        self.set_ui_state("disabled")
        self.status_label.configure(text="Mesclando... Por favor, aguarde.")

        # Executa a mesclagem em uma thread separada para não travar a UI
        merge_thread = threading.Thread(target=self._execute_merge, args=(save_path,))
        merge_thread.start()

    def _execute_merge(self, save_path):
        """
        Lógica da mesclagem (executada em uma thread secundária).
        Esta função NÃO deve interagir diretamente com a UI.
        """
        try:
            # --- LÓGICA DE MESCLAGEM ---
            # Esta parte é pesada e fica na thread secundária.
            merger = PdfWriter()
            total_files = len(self.pdf_files)
            for i, pdf_path in enumerate(self.pdf_files):
                # O feedback de progresso também precisa ser agendado na thread principal
                filename = os.path.basename(pdf_path)
                self.after(0, lambda fn=filename, num=i+1, total=total_files: self.status_label.configure(text=f"Processando {num}/{total}: {fn}..."))

                with open(pdf_path, "rb") as f:
                    merger.append(f)
            
            self.status_label.configure(text="Finalizando e salvando o arquivo...")
            merger.write(save_path)
            merger.close()

            # Agenda a função de sucesso para ser executada na thread principal
            self.after(0, self._handle_merge_result, save_path, None)
        
        except Exception as e:
            # Agenda a função de erro para ser executada na thread principal
            self.after(0, self._handle_merge_result, None, e)

    def _handle_merge_result(self, save_path, error):
        """
        Lida com o resultado da mesclagem na thread principal da UI.
        """
        if error:
            self.status_label.configure(text=f"Erro: {error}", text_color="red")
            messagebox.showerror("Erro na Mesclagem", f"Ocorreu um erro ao mesclar os PDFs:\n\n{error}")
        else:
            self.status_label.configure(text=f"Sucesso! PDF salvo em: {os.path.basename(save_path)}", text_color="green")
            messagebox.showinfo("Sucesso", "Os arquivos PDF foram mesclados com sucesso!")
            self.pdf_files.clear()
        
        # Reseta o estado da UI em ambos os casos (sucesso ou erro)
        self.is_merging = False
        self.set_ui_state("normal")
        self.after(5000, lambda: self.status_label.configure(text_color=self.default_status_text_color)) # Reseta a cor após 5s

    def set_ui_state(self, state):
        """Desabilita ou habilita os elementos da UI durante o processamento."""
        self.add_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.merge_button.configure(state=state)
        
        # Desabilita os botões de reordenar/deletar
        for file_frame in self.scrollable_frame.winfo_children():
            # Acessa o frame dos botões dentro do frame do arquivo
            button_container = file_frame.winfo_children()[1]
            for button in button_container.winfo_children():
                button.configure(state=state)
        
        # Garante que o estado dos botões seja reavaliado corretamente ao final
        if state == "normal":
            self.update_file_list_ui()

if __name__ == "__main__":
    app = App()
    app.mainloop()