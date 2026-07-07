import { Layout } from "./components/Layout/Layout";
import { NotesInputSection } from "./features/notes-input/components/NotesInputSection";
import { TasksSection } from "./features/tasks/components/TasksSection";

function App() {
  return (
    <Layout>
      <NotesInputSection />
      <TasksSection />
    </Layout>
  );
}

export default App;
