// AY ESCREVA — site oficial. Menu em telas pequenas, sugestão de download e cópia do SHA-256.
// Nenhum dado é enviado a lugar nenhum. SPDX-License-Identifier: MPL-2.0
(function () {
  var botao = document.querySelector('.menu-botao');
  var menu = document.getElementById('menu-principal');
  if (botao && menu) {
    botao.addEventListener('click', function () {
      var aberto = menu.classList.toggle('aberto');
      botao.setAttribute('aria-expanded', aberto ? 'true' : 'false');
    });
  }

  // Sugestão de download: só destaca; todas as versões continuam listadas.
  var alvo = document.getElementById('sugestao');
  if (alvo) {
    var ua = navigator.userAgent || '';
    var plataforma = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || '';
    function sugerir(id, texto) {
      var item = document.querySelector('[data-plataforma="' + id + '"]');
      if (item) item.classList.add('sugerida');
      alvo.textContent = texto;
      alvo.hidden = false;
    }
    if (/Windows/i.test(plataforma) || /Windows NT/i.test(ua)) {
      sugerir('windows11-x64', 'Detectamos o Windows. A versão para Windows 11 de 64 bits está destacada abaixo.');
      if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
        navigator.userAgentData.getHighEntropyValues(['platformVersion', 'architecture']).then(function (v) {
          var maior = parseInt((v.platformVersion || '0').split('.')[0], 10);
          if (v.architecture === 'arm') {
            sugerir('windows-arm64', 'Seu Windows parece ser ARM. A versão para ARM ainda está em desenvolvimento; veja todas as opções abaixo.');
          } else if (maior > 0 && maior < 13) {
            sugerir('windows10-x64', 'Seu computador parece usar o Windows 10. A versão para Windows 10 ainda está em desenvolvimento: o instalador atual só funciona no Windows 11.');
          }
        }).catch(function () {});
      }
    } else if (/Mac/i.test(plataforma)) {
      sugerir('macos', 'Detectamos um Mac. A versão para macOS ainda está em desenvolvimento.');
    } else if (/Linux|X11/i.test(plataforma)) {
      sugerir('linux', 'Detectamos o Linux. A versão para Linux ainda está em desenvolvimento.');
    } else if (/Android|iPhone|iPad/i.test(ua)) {
      alvo.textContent = 'O AY ESCREVA é um aplicativo para computador. Você pode baixar o instalador aqui e usá-lo no seu computador com Windows 11.';
      alvo.hidden = false;
    }
  }

  document.querySelectorAll('[data-copiar]').forEach(function (b) {
    b.addEventListener('click', function () {
      var texto = document.getElementById(b.getAttribute('data-copiar')).textContent.trim();
      if (navigator.clipboard) {
        navigator.clipboard.writeText(texto).then(function () { b.textContent = 'Copiado'; setTimeout(function () { b.textContent = 'Copiar'; }, 1800); });
      }
    });
  });
})();
