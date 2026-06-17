import { useLocation } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { Yomineko } from "~/ui/yomineko/mascot";

const INFO: Record<string, { title: string; active: string; icon: string; blurb: string }> = {
  "/revisar": { title: "Revisar", active: "review", icon: "style", blurb: "A revisão espaçada das suas lições aparece aqui. Em breve no protótipo." },
  "/pratica": { title: "Prática", active: "practice", icon: "target", blurb: "Os seis modos de prática (kana, partículas, frases, conjugação, números) entram aqui." },
  "/perfil": { title: "Perfil", active: "profile", icon: "person", blurb: "Seu progresso, conquistas e ajustes ficam aqui." },
};

export function meta() {
  return [{ title: "Yomineko — Em breve" }];
}

export default function Soon() {
  const { pathname } = useLocation();
  const info = INFO[pathname] ?? { title: "Em breve", active: "home", icon: "hourglass_empty", blurb: "Esta área ainda está em construção no protótipo." };
  return (
    <AppShell active={info.active} title={info.title}>
      <div className="ym-page">
        <div className="ym-empty">
          <Yomineko pose="sleep" size={160} />
          <div className="ym-empty-icon"><Icon name={info.icon} size={22} color="var(--primary)" /></div>
          <h1 className="ym-h1" style={{ marginTop: 8 }}>{info.title}</h1>
          <p className="ym-sub" style={{ maxWidth: 420, margin: "8px auto 0" }}>{info.blurb}</p>
        </div>
      </div>
    </AppShell>
  );
}
