// AY ESCREVA - lançador do aplicativo para Windows.
// Abre o editor (motor de documentos em program\soffice.exe) já no modo de texto,
// repassando arquivos recebidos pela linha de comando ou pelo Explorador.
// Compilado com o csc do .NET Framework 4.x, presente no Windows 10 e 11.
// SPDX-License-Identifier: MPL-2.0
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;

[assembly: AssemblyTitle("AY ESCREVA")]
[assembly: AssemblyProduct("AY ESCREVA")]
[assembly: AssemblyDescription("Editor de textos AY ESCREVA")]
[assembly: AssemblyCompany("Projeto AY ESCREVA")]
[assembly: AssemblyCopyright("Projeto AY ESCREVA - MPL-2.0")]
[assembly: AssemblyVersion(AYEscreva.Lancador.Versao)]
[assembly: AssemblyFileVersion(AYEscreva.Lancador.Versao)]

namespace AYEscreva
{
    internal static class Lancador
    {
        public const string Versao = "0.1.0.0";

        [STAThread]
        private static int Main(string[] args)
        {
            string pastaApp = AppDomain.CurrentDomain.BaseDirectory;
            string motor = Path.Combine(pastaApp, "program", "soffice.exe");
            if (!File.Exists(motor))
            {
                Erro("Não foi possível encontrar os componentes do editor em:\n" + motor +
                     "\n\nReinstale o AY ESCREVA.");
                return 2;
            }

            var argumentos = new StringBuilder();
            bool temArquivo = false;
            foreach (string a in args)
            {
                if (a.StartsWith("-") || a.StartsWith("/"))
                {
                    // Opções do lançador
                    if (a == "--versao" || a == "/?")
                    {
                        MessageBox.Show("AY ESCREVA " + Versao, "AY ESCREVA", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        return 0;
                    }
                    // Opções conhecidas do motor que fazem sentido para o usuário
                    if (a == "--safe-mode" || a == "--norestore" || a == "-p" || a == "--pt" || a == "-o" || a == "-n")
                    {
                        argumentos.Append(' ').Append(a);
                        continue;
                    }
                    continue; // demais opções são ignoradas por segurança
                }
                temArquivo = true;
                argumentos.Append(' ').Append(Citar(Path.GetFullPath(a)));
            }

            string linha = temArquivo ? argumentos.ToString().TrimStart() : ("--writer" + argumentos.ToString());
            try
            {
                var psi = new ProcessStartInfo(motor, linha)
                {
                    UseShellExecute = false,
                    WorkingDirectory = pastaApp
                };
                Process.Start(psi);
                return 0;
            }
            catch (Exception ex)
            {
                Erro("Não foi possível iniciar o editor.\n\n" + ex.Message);
                return 1;
            }
        }

        private static string Citar(string s)
        {
            // Regras de citação do CommandLineToArgvW
            if (s.Length > 0 && s.IndexOfAny(new[] { ' ', '\t', '"' }) < 0) return s;
            var sb = new StringBuilder("\"");
            int barras = 0;
            foreach (char c in s)
            {
                if (c == '\\') { barras++; continue; }
                if (c == '"') { sb.Append('\\', barras * 2 + 1).Append('"'); barras = 0; continue; }
                sb.Append('\\', barras).Append(c); barras = 0;
            }
            sb.Append('\\', barras * 2).Append('"');
            return sb.ToString();
        }

        private static void Erro(string msg)
        {
            MessageBox.Show(msg, "AY ESCREVA", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
