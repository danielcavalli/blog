// The site's own words, in each language it speaks.

export type Lang = "en" | "pt";

export const WORDS = {
  en: {
    places: { blog: "blog", about: "about", cv: "cv" },
    landing: { voice: "Daniel Cavalli · machine learning engineer", blog: "Blog", about: "About Me", cv: "CV", latest: "latest" },
    index: { title: "Latest Posts", sortBy: "sort by", published: "Published At", updated: "Last Updated", filter: "Filter", latest: "latest", search: "search", searchFor: "a word, a name, a tag", found: "found", nothing: "Nothing found.", nothingHelp: "Try another word, or fewer of them." },
    post: { back: "Back to Blog", contents: "On this page" },
    deck: { previous: "previous slide", next: "next slide", full: "full screen", leave: "leave full screen", where: "slide {n} of {total}" },
    about: { title: "About", fact: "dan.rio" },
    cv: { fact: "curriculum vitae", contact: "Contact", summary: "Summary", experience: "Experience", skills: "Skills", education: "Education", languages: "Languages" },
    posts: (count: number) => `${count} ${count === 1 ? "post" : "posts"}`,
    missing: { title: "This page isn't here.", help: "It may have moved when the site was rebuilt. The blog has every post." },
    foot: "© Daniel Cavalli · writing under CC BY 4.0",
    description: "Daniel Cavalli on machine learning engineering, AI agents, and the software he builds for himself.",
  },
  pt: {
    places: { blog: "blog", about: "sobre", cv: "cv" },
    landing: { voice: "Daniel Cavalli · engenheiro de machine learning", blog: "Blog", about: "Sobre mim", cv: "CV", latest: "o mais recente em" },
    index: { title: "Posts Recentes", sortBy: "ordenar por", published: "Data de Publicação", updated: "Última Atualização", filter: "Filtrar", latest: "mais recente", search: "buscar", searchFor: "uma palavra, um nome, uma tag", found: "encontrados", nothing: "Nada encontrado.", nothingHelp: "Tente outra palavra, ou menos palavras." },
    post: { back: "Voltar ao Blog", contents: "Neste artigo" },
    deck: { previous: "slide anterior", next: "próximo slide", full: "tela cheia", leave: "sair da tela cheia", where: "slide {n} de {total}" },
    about: { title: "Sobre", fact: "dan.rio" },
    cv: { fact: "curriculum vitae", contact: "Contato", summary: "Resumo", experience: "Experiência", skills: "Habilidades", education: "Formação", languages: "Idiomas" },
    posts: (count: number) => `${count} ${count === 1 ? "post" : "posts"}`,
    missing: { title: "Esta página não está aqui.", help: "Ela pode ter mudado de lugar quando o site foi refeito. O blog tem todos os posts." },
    foot: "© Daniel Cavalli · textos sob CC BY 4.0",
    description: "Daniel Cavalli sobre engenharia de machine learning, agentes de IA e o software que constrói para si mesmo.",
  },
} as const;

/** The same page in each language it exists in. */
export type Alternates = Partial<Record<Lang, string>>;
