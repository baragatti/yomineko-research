import { redirect } from "react-router";

/** See routes/redirectCurso.ts — /falar now lives at /cursos/falar. */
export async function loader() {
  return redirect("/cursos/falar", 301);
}
