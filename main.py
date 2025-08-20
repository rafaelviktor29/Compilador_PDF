import customtkinter as ctk
from tkinter import filedialog, messagebox, Listbox, Scrollbar
from pypdf import PdfWriter
import os
import threading

class PDFMergerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Configurações da Janela Principal ---
        self.title("Compilador de PDF")
        self.geometry("600x500")
        
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.file_paths = []

        # --- Configuração do Layout em Grid ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # --- Frame dos Botões de Controle ---
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.btn_add = ctk.CTkButton(control_frame, text="Adicionar PDFs", command=self.select_files)
        self.btn_add.pack(side="left", padx=5, pady=5)

        self.btn_remove = ctk.CTkButton(control_frame, text="Remover", command=self.remove_selected)
        self.btn_remove.pack(side="left", padx=5, pady=5)
        
        self.btn_up = ctk.CTkButton(control_frame, text="Mover p/ Cima", command=self.move_up)
        self.btn_up.pack(side="left", padx=5, pady=5)

        self.btn_down = ctk.CTkButton(control_frame, text="Mover p/ Baixo", command=self.move_down)
        self.btn_down.pack(side="left", padx=5, pady=5)
        
        # <--- NOVO: Botão para limpar a lista ---
        self.btn_clear = ctk.CTkButton(control_frame, text="Limpar Lista", command=self.clear_list, fg_color="#D32F2F", hover_color="#B71C1C")
        self.btn_clear.pack(side="left", padx=5, pady=5)
        
        # --- Frame da Lista de Arquivos ---
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.listbox = Listbox(
            list_frame, 
            selectmode="single", 
            bg="#2D2D2D",
            fg="white",
            selectbackground="#1F6AA5",
            borderwidth=0, 
            highlightthickness=0,
            font=("Arial", 12)
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # --- Botão Principal de Compilação ---
        self.btn_compile = ctk.CTkButton(
            self, 
            text="Compilar PDFs e Salvar", 
            font=("Arial", 14, "bold"), 
            command=self.start_merge_thread  # Chama a função que inicia a thread
        )
        self.btn_compile.grid(row=2, column=0, padx=10, pady=10, sticky="ew", ipady=5)

    def update_listbox(self):
        """Limpa e atualiza a lista de exibição com os nomes dos arquivos."""
        self.listbox.delete(0, "end")
        for path in self.file_paths:
            self.listbox.insert("end", os.path.basename(path))

    def select_files(self):
        """Abre a janela para o usuário selecionar múltiplos arquivos PDF."""
        files = filedialog.askopenfilenames(
            title="Selecione os arquivos PDF",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if files:
            self.file_paths.extend(list(files))
            self.update_listbox()

    def remove_selected(self):
        """Remove o arquivo atualmente selecionado na lista."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para remover.")
            return
        
        index = selected_indices[0]
        self.file_paths.pop(index)
        self.update_listbox()

    def move_up(self):
        """Move o arquivo selecionado uma posição para cima na lista."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para mover.")
            return

        pos = selected_indices[0]
        if pos == 0:
            return

        self.file_paths[pos], self.file_paths[pos - 1] = self.file_paths[pos - 1], self.file_paths[pos]
        self.update_listbox()
        self.listbox.select_set(pos - 1)
        self.listbox.activate(pos - 1)

    def move_down(self):
        """Move o arquivo selecionado uma posição para baixo na lista."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para mover.")
            return
            
        pos = selected_indices[0]
        if pos == len(self.file_paths) - 1:
            return

        self.file_paths[pos], self.file_paths[pos + 1] = self.file_paths[pos + 1], self.file_paths[pos]
        self.update_listbox()
        self.listbox.select_set(pos + 1)
        self.listbox.activate(pos + 1)

    # Função para limpar a lista
    def clear_list(self):
        """Limpa todos os arquivos da lista."""
        # Pede confirmação ao usuário
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar a lista de arquivos?"):
            self.file_paths.clear()
            self.update_listbox()

    # Função para habilitar/desabilitar botões durante a compilação
    def toggle_controls(self, state="normal"):
        """Altera o estado de todos os botões."""
        self.btn_add.configure(state=state)
        self.btn_remove.configure(state=state)
        self.btn_up.configure(state=state)
        self.btn_down.configure(state=state)
        self.btn_clear.configure(state=state)
        self.btn_compile.configure(state=state)

    # Esta função agora APENAS inicia a thread
    def start_merge_thread(self):
        """Inicia o processo de compilação em uma thread separada para não travar a UI."""
        if len(self.file_paths) < 2:
            messagebox.showwarning("Aviso", "Você precisa de pelo menos 2 arquivos para compilar.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Salvar PDF compilado como...",
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )

        if not output_path:
            return

        # Desabilita os botões e atualiza o texto para dar feedback ao usuário
        self.toggle_controls(state="disabled")
        self.btn_compile.configure(text="Compilando...")

        # Cria e inicia a thread, passando a função de compilação e seus argumentos
        merge_thread = threading.Thread(
            target=self.merge_pdfs_worker, 
            args=(self.file_paths.copy(), output_path)
        )
        merge_thread.start()

    # Esta é a função que roda na thread separada
    def merge_pdfs_worker(self, file_paths, output_path):
        """Pega a lista de arquivos e os compila. Executado em segundo plano."""
        try:
            merger = PdfWriter()
            for pdf_path in file_paths:
                merger.append(pdf_path)
            
            merger.write(output_path)
            merger.close()
            
            # As chamadas de messagebox devem ser feitas na thread principal
            # self.after(0, ...) agenda a execução da função na thread principal
            self.after(0, lambda: messagebox.showinfo("Sucesso", f"PDFs compilados com sucesso!\n\nSalvo em: {output_path}"))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Ocorreu um erro ao compilar os PDFs:\n\n{e}"))

        finally:
            # Independentemente de sucesso ou erro, reabilita os botões na thread principal
            self.after(0, self.toggle_controls, "normal")
            self.after(0, lambda: self.btn_compile.configure(text="Compilar PDFs e Salvar"))


# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = PDFMergerApp()
    app.mainloop()