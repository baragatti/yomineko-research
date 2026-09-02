import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("health", "routes/health.ts"),
  route("entrar", "routes/login.tsx"),
  // Two paths through one corpus. /cursos is the chooser; each path keeps its own index below it.
  route("cursos", "routes/courses.tsx"),
  route("cursos/jlpt", "routes/course.tsx"),
  route("cursos/falar", "routes/speak.tsx"),
  // Old top-level addresses, kept as permanent redirects.
  route("curso", "routes/redirectCurso.ts"),
  route("curso/:topicId", "routes/topic.tsx"),
  route("licao/:lessonId", "routes/lesson.tsx"),
  route("kana", "routes/kana.tsx"),
  route("kanji", "routes/kanji.tsx"),
  route("kanji/:char", "routes/kanjiDetail.tsx"),
  route("vocabulario", "routes/vocab.tsx"),
  route("vocabulario/:id", "routes/vocabDetail.tsx"),
  route("gramatica", "routes/grammar.tsx"),
  route("gramatica/:key", "routes/grammarDetail.tsx"),
  route("revisar", "routes/review.tsx"),
  route("pratica", "routes/practice.tsx"),
  route("pratica/conjugacao", "routes/conjugationDrill.tsx"),
  route("pratica/papeis", "routes/roleDrill.tsx"),
  route("pratica/:mode", "routes/practiceSession.tsx"),
  route("simulado", "routes/exam.tsx"),
  // Static segment before the dynamic one: "estudo" is three segments deep, so it can never be
  // mistaken for a level by `simulado/:level`.
  route("simulado/estudo/:lessonId", "routes/examStudy.tsx"),
  route("simulado/:level", "routes/examPaper.tsx"),
  route("falar", "routes/redirectFalar.ts"),
  route("falar/:stage/:unit", "routes/speakUnit.tsx"),
  route("perfil", "routes/soon.tsx", { id: "perfil" }),
  route("creditos", "routes/creditos.tsx"),
] satisfies RouteConfig;
