import { redirect } from "react-router";

/**
 * /curso and /falar were separate top-level destinations before the two paths were put side by side
 * under /cursos. Old links (and anything a learner bookmarked) still resolve, permanently, rather than
 * 404ing — a moved page that forgets its old address is a broken page.
 */
export async function loader() {
  return redirect("/cursos/jlpt", 301);
}
