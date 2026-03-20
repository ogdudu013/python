import { GoogleGenerativeAI } from "@google/generative-ai"; // O pacote correto é este

// 1. Coloque sua chave diretamente aqui para testar (ou use process.env.API_KEY)
const genAI = new GoogleGenerativeAI("AIzaSyAfiyvoVXDIestmwW-B4bh7a-gfS0LkZSU");

async function main() {
  // 2. Use um modelo existente (o gemini-3 ainda não está disponível via SDK comum)
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

  try {
    const result = await model.generateContent("Explique como IA funciona em poucas palavras.");
    const response = await result.response;
    console.log(response.text());
  } catch (error) {
    console.error("Erro detalhado:", error);
  }
}

main();
