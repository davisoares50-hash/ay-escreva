// Leitura e acionamento da árvore de acessibilidade MSAA (a mesma interface que leitores de tela como o NVDA
// usam, junto com IAccessible2). Usado pelos testes de interface do AY ESCREVA.
// SPDX-License-Identifier: MPL-2.0
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using Accessibility;

public static class Msaa
{
    [DllImport("oleacc.dll")]
    static extern int AccessibleObjectFromWindow(IntPtr hwnd, uint id, ref Guid iid, [MarshalAs(UnmanagedType.Interface)] out object ppv);
    [DllImport("oleacc.dll")]
    static extern int AccessibleChildren(IAccessible acc, int start, int count, [Out] object[] children, out int obtained);
    [DllImport("oleacc.dll", CharSet = CharSet.Unicode)]
    static extern uint GetRoleText(uint role, StringBuilder text, uint max);

    const uint OBJID_CLIENT = 0xFFFFFFFC;
    static Guid IID_IAccessible = new Guid("618736E0-3C3D-11CF-810C-00AA00389B71");

    public class No
    {
        public IAccessible Acc; public object Filho; public string Nome; public string Papel; public int Estado; public int Nivel;
        public string Caminho; public string Descricao; public string Atalho;
        public bool Visivel { get { return (Estado & 0x8000) == 0; } }        // STATE_SYSTEM_INVISIBLE
        public bool Desativado { get { return (Estado & 0x1) != 0; } }        // STATE_SYSTEM_UNAVAILABLE
        public bool Marcado { get { return (Estado & 0x10) != 0; } }          // STATE_SYSTEM_CHECKED
        public bool Pressionado { get { return (Estado & 0x8) != 0; } }       // STATE_SYSTEM_PRESSED
        public bool Selecionado { get { return (Estado & 0x2) != 0; } }       // STATE_SYSTEM_SELECTED
        public void Acionar() { Acc.accDoDefaultAction(Filho); }
        public void Focar() { Acc.accSelect(1, Filho); }                    // SELFLAG_TAKEFOCUS
    }

    public static IAccessible Raiz(IntPtr hwnd)
    {
        object o;
        int hr = AccessibleObjectFromWindow(hwnd, OBJID_CLIENT, ref IID_IAccessible, out o);
        if (hr != 0) throw new Exception("AccessibleObjectFromWindow falhou: 0x" + hr.ToString("x"));
        return (IAccessible)o;
    }

    static string Papel(object r)
    {
        if (r is int) { var sb = new StringBuilder(128); GetRoleText((uint)(int)r, sb, 128); return sb.ToString(); }
        return r == null ? "" : r.ToString();
    }

    static T Seguro<T>(Func<T> f, T padrao) { try { return f(); } catch { return padrao; } }

    public static List<No> Listar(IntPtr hwnd, int profundidade)
    {
        var lista = new List<No>();
        Visitar(Raiz(hwnd), 0, profundidade, "", lista);
        return lista;
    }

    static void Visitar(IAccessible acc, int nivel, int max, string caminho, List<No> lista)
    {
        if (nivel > max) return;
        int n = Seguro(() => acc.accChildCount, 0);
        if (n <= 0) return;
        var filhos = new object[n];
        int obtidos;
        if (AccessibleChildren(acc, 0, n, filhos, out obtidos) != 0) return;
        for (int i = 0; i < obtidos; i++)
        {
            object f = filhos[i];
            IAccessible fa = f as IAccessible;
            IAccessible alvo = fa ?? acc;
            object id = fa != null ? (object)0 : f;
            var no = new No
            {
                Acc = alvo, Filho = id, Nivel = nivel,
                Nome = Seguro(() => alvo.get_accName(id), "") ?? "",
                Papel = Papel(Seguro(() => alvo.get_accRole(id), null)),
                Estado = Seguro(() => Convert.ToInt32(alvo.get_accState(id)), 0),
                Descricao = Seguro(() => alvo.get_accDescription(id), "") ?? "",
                Atalho = Seguro(() => alvo.get_accKeyboardShortcut(id), "") ?? ""
            };
            no.Caminho = caminho + "/" + no.Nome;
            lista.Add(no);
            if (fa != null) Visitar(fa, nivel + 1, max, no.Caminho, lista);
        }
    }
}
