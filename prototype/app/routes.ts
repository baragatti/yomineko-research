import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("health", "routes/health.ts"),
  route("entrar", "routes/login.tsx"),
  route("curso", "routes/course.tsx"),
  route("curso/:topicId", "routes/topic.tsx"),
  route("licao/:lessonId", "routes/lesson.tsx"),
  route("kanji", "routes/kanji.tsx"),
  route("kanji/:char", "routes/kanjiDetail.tsx"),
  route("vocabulario", "routes/vocab.tsx"),
  route("vocabulario/:headword", "routes/vocabDetail.tsx"),
  route("gramatica", "routes/grammar.tsx"),
  route("gramatica/:key", "routes/grammarDetail.tsx"),
  route("revisar", "routes/review.tsx"),
  route("pratica", "routes/practice.tsx"),
  route("pratica/:mode", "routes/practiceSession.tsx"),
  route("perfil", "routes/soon.tsx", { id: "perfil" }),
] satisfies RouteConfig;
