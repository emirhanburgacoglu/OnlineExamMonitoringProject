// Data/Exam.cs
using System.ComponentModel.DataAnnotations;

namespace Dashboard.Web.Data
{
    public class Exam
    {
        public int Id { get; set; }
        public string CourseName { get; set; } = string.Empty;
        public DateTime StartTime { get; set; }

        // Bir sınavda birden fazla olay olabilir
        public ICollection<EventLog> EventLogs { get; set; } = new List<EventLog>();
    }
}