import WindAnalyzer from '@/components/WindAnalyzer';

export default function Home() {
  return (
    <main className="p-10">
      <h1 className="text-2xl font-bold text-center mb-8">WindLab 3D Plotter</h1>
      <WindAnalyzer />
    </main>
  );
}