import customtkinter as ctk
from tkinter import filedialog, messagebox, Listbox, Scrollbar
from pypdf import PdfWriter
import os


class PDFMergerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Configurações da Janela Principal ---
        self.title("Compilador de PDF")
        self.geometry("600x500")
        
        # Define o tema (System, Dark, Light)
        ctk.set_appearance_mode("System")
        # Define o tema de cores dos widgets
        ctk.set_default_color_theme("blue")

        # Armazena os caminhos completos dos arquivos na ordem correta
        self.file_paths = []

        # --- Configuração do Layout em Grid ---
        # A coluna 0 e a linha 1 vão se expandir para preencher o espaço
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
        
        # --- Frame da Lista de Arquivos ---
        # CustomTkinter ainda não tem um widget Listbox, então uso do Tkinter padrão
        # e o estilizamos para combinar com o tema escuro/claro.
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.listbox = Listbox(
            list_frame, 
            selectmode="single", 
            bg="#2D2D2D",  # Cor de fundo para tema escuro
            fg="white",  # Cor do texto para tema escuro
            selectbackground="#1F6AA5",  # Cor de fundo do item selecionado
            borderwidth=0, 
            highlightthickness=0,
            font=("Arial", 12)
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")

        # Barra de rolagem para a lista
        scrollbar = Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # --- Botão Principal de Compilação ---
        self.btn_compile = ctk.CTkButton(
            self, 
            text="Compilar PDFs e Salvar", 
            font=("Arial", 14, "bold"), 
            command=self.merge_pdfs
        )
        self.btn_compile.grid(row=2, column=0, padx=10, pady=10, sticky="ew", ipady=5)

    def update_listbox(self):
        """Limpa e atualiza a lista de exibição com os nomes dos arquivos."""
        self.listbox.delete(0, "end")
        for path in self.file_paths:
            # Mostra apenas o nome do arquivo, não o caminho completo, para uma UI mais limpa
            self.listbox.insert("end", os.path.basename(path))

    def select_files(self):
        """Abre a janela para o usuário selecionar múltiplos arquivos PDF."""
        files = filedialog.askopenfilenames(
            title="Selecione os arquivos PDF",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if files:
            # Adiciona os novos arquivos à lista de caminhos
            self.file_paths.extend(list(files))
            self.update_listbox()

    def remove_selected(self):
        """Remove o arquivo atualmente selecionado na lista."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para remover.")
            return
        
        # O índice do item selecionado
        index = selected_indices[0]
        
        # Remove o caminho do arquivo da nossa lista de dados
        self.file_paths.pop(index)
        
        self.update_listbox()

    def move_up(self):
        """Move o arquivo selecionado uma posição para cima na lista."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para mover.")
            return

        pos = selected_indices[0]
        # Não pode mover se já for o primeiro
        if pos == 0:
            return

        # Troca o item com o item anterior na lista de caminhos
        self.file_paths[pos], self.file_paths[pos - 1] = self.file_paths[pos - 1], self.file_paths[pos]
        
        self.update_listbox()
        
        # Mantém a seleção no item que foi movido
        self.listbox.select_set(pos - 1)
        self.listbox.activate(pos - 1)

    def move_down(self):
        """Move o arquivo selecionado uma posição para baixo na lista."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para mover.")
            return
            
        pos = selected_indices[0]
        # Não pode mover se já for o último
        if pos == len(self.file_paths) - 1:
            return

        # Troca o item com o item seguinte na lista de caminhos
        self.file_paths[pos], self.file_paths[pos + 1] = self.file_paths[pos + 1], self.file_paths[pos]
        
        self.update_listbox()
        
        # Mantém a seleção no item que foi movido
        self.listbox.select_set(pos + 1)
        self.listbox.activate(pos + 1)

    def merge_pdfs(self):
        """Pega todos os arquivos da lista, compila-os e pede ao usuário para salvar."""
        if len(self.file_paths) < 2:
            messagebox.showwarning("Aviso", "Você precisa de pelo menos 2 arquivos para compilar.")
            return

        # Pede ao usuário onde salvar o arquivo final
        output_path = filedialog.asksaveasfilename(
            title="Salvar PDF compilado como...",
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )

        # Se o usuário cancelar a janela de salvar, não faz nada
        if not output_path:
            return

        # Cria o objeto que fará a união
        merger = PdfWriter()
        
        try:
            # Adiciona cada PDF da lista (na ordem correta) ao objeto merger
            for pdf_path in self.file_paths:
                merger.append(pdf_path)

            # Escreve o arquivo final no disco
            merger.write(output_path)
            merger.close()
            
            messagebox.showinfo("Sucesso", f"PDFs compilados com sucesso!\n\nSalvo em: {output_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao compilar os PDFs:\n\n{e}")

# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = PDFMergerApp()
    app.mainloop()