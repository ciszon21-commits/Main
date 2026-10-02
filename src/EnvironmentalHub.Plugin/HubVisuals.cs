using Eto.Drawing;
using Eto.Forms;

namespace EnvironmentalHub.Plugin;

internal enum HubTopic { Overview, Model, Environment, Settings, Run, Results, Compare }
internal enum HubGlyph { Overview, Model, Weather, Settings, Run, Results, Compare, Location, Time, Solar }

// Categorical interface colors; these never modify a solver palette or mesh.
internal static class HubVisuals
{
    internal static bool Dark => SystemColors.ControlBackground.R * .2126 + SystemColors.ControlBackground.G * .7152 + SystemColors.ControlBackground.B * .0722 < .5;
    internal static Color Accent(HubTopic topic) => Palette(topic, Dark);
    private static Color Rgb(int hex) => Color.FromArgb((hex >> 16) & 255, (hex >> 8) & 255, hex & 255);
    internal static Color Palette(HubTopic topic, bool dark) => Rgb((topic, dark) switch
    {
        (HubTopic.Model, false) => 0x3E5D72, (HubTopic.Model, true) => 0xAAC2D2,
        (HubTopic.Environment, false) => 0x226B61, (HubTopic.Environment, true) => 0x8ECBBF,
        (HubTopic.Settings, false) => 0x58528B, (HubTopic.Settings, true) => 0xBBB1E0,
        (HubTopic.Run, false) => 0x8A652E, (HubTopic.Run, true) => 0xD4B778,
        (HubTopic.Results, false) => 0x48585A, (HubTopic.Results, true) => 0xB5C7C9,
        (HubTopic.Compare, false) => 0x73506E, (HubTopic.Compare, true) => 0xD2B0CA,
        (_, false) => 0x4B5865, (_, true) => 0xB8C5D0
    });
    internal static Color Secondary => Dark ? Rgb(0xBBC2C8) : Rgb(0x5D6872);
    internal static Color Rule(HubTopic topic)
    {
        var a = Accent(topic); var b = SystemColors.ControlBackground;
        return new Color(b.R * .7f + a.R * .3f, b.G * .7f + a.G * .3f, b.B * .7f + a.B * .3f);
    }
    internal static HubGlyph Glyph(HubTopic topic) => topic switch
    {
        HubTopic.Model => HubGlyph.Model, HubTopic.Environment => HubGlyph.Weather,
        HubTopic.Settings => HubGlyph.Settings, HubTopic.Run => HubGlyph.Run,
        HubTopic.Results => HubGlyph.Results, HubTopic.Compare => HubGlyph.Compare,
        _ => HubGlyph.Overview
    };
    internal static HubTopic ModuleTopic(Type type) => type == typeof(RadiationPanel) || type == typeof(SunPathPanel) ? HubTopic.Run :
        type == typeof(TimePanel) ? HubTopic.Settings : type == typeof(HubOverviewPanel) ? HubTopic.Overview : HubTopic.Environment;
    internal static HubGlyph ModuleGlyph(Type type) => type == typeof(RadiationPanel) || type == typeof(SunPathPanel) ? HubGlyph.Solar :
        type == typeof(TimePanel) ? HubGlyph.Time : type == typeof(LocationPanel) ? HubGlyph.Location :
        type == typeof(HubOverviewPanel) ? HubGlyph.Overview : HubGlyph.Weather;

    internal static Drawable Icon(HubGlyph glyph, HubTopic topic, int size = 20)
    {
        var icon = new Drawable { Size = new Size(size, size), CanFocus = false, ToolTip = topic.ToString() };
        icon.Paint += (_, e) =>
        {
            var g = e.Graphics; g.ScaleTransform(size / 24f);
            using var p = new Pen(Accent(topic), 1.5f);
            void Line(float x1, float y1, float x2, float y2) => g.DrawLine(p, x1, y1, x2, y2);
            void Chain(params PointF[] points) => g.DrawLines(p, points);
            switch (glyph)
            {
                case HubGlyph.Model:
                    Chain(new(12, 3), new(21, 8), new(21, 17), new(12, 22), new(3, 17), new(3, 8), new(12, 3));
                    Chain(new(3, 8), new(12, 13), new(21, 8)); Line(12, 13, 12, 22); break;
                case HubGlyph.Weather:
                    using (var cloud = new GraphicsPath())
                    {
                        cloud.MoveTo(6, 18); cloud.LineTo(18, 18);
                        cloud.AddBezier(new(18, 18), new(24, 18), new(24, 10), new(18, 10));
                        cloud.AddBezier(new(18, 10), new(16, 2), new(8, 2), new(8, 10));
                        cloud.AddBezier(new(8, 10), new(1, 8), new(0, 18), new(6, 18));
                        cloud.CloseFigure(); g.DrawPath(p, cloud);
                    }
                    Line(8, 21, 10, 21); Line(14, 21, 16, 21); break;
                case HubGlyph.Settings:
                    foreach (var (y, knob) in new[] { (6, 8), (12, 16), (18, 11) })
                    { Line(3, y, knob - 2, y); Line(knob + 2, y, 21, y); g.DrawRectangle(p, knob - 2, y - 2, 4, 4); }
                    break;
                case HubGlyph.Run:
                    Chain(new(6, 4), new(20, 12), new(6, 20), new(6, 4)); break;
                case HubGlyph.Results:
                    g.DrawRectangle(p, 4, 14, 3, 6); g.DrawRectangle(p, 10, 9, 3, 11); g.DrawRectangle(p, 16, 4, 3, 16);
                    Line(3, 22, 21, 22); break;
                case HubGlyph.Compare:
                    g.DrawRectangle(p, 3, 4, 18, 16); Line(12, 4, 12, 20);
                    Line(6, 9, 9, 9); Line(6, 14, 9, 14); Line(15, 9, 18, 9); Line(15, 14, 18, 14); break;
                case HubGlyph.Time:
                    g.DrawEllipse(p, 4, 4, 16, 16); Chain(new(12, 7), new(12, 12), new(16, 14)); break;
                case HubGlyph.Location:
                    using (var pin = new GraphicsPath())
                    {
                        pin.MoveTo(12, 22);
                        pin.AddBezier(new(12, 22), new(1, 12), new(3, 3), new(12, 3));
                        pin.AddBezier(new(12, 3), new(21, 3), new(23, 12), new(12, 22));
                        pin.CloseFigure(); g.DrawPath(p, pin);
                    }
                    g.DrawEllipse(p, 9, 7, 6, 6); break;
                case HubGlyph.Solar:
                    g.DrawEllipse(p, 8, 8, 8, 8);
                    Line(12, 2, 12, 5); Line(12, 19, 12, 22); Line(2, 12, 5, 12); Line(19, 12, 22, 12);
                    Line(5, 5, 7, 7); Line(17, 17, 19, 19); Line(5, 19, 7, 17); Line(17, 7, 19, 5); break;
                default:
                    foreach (var (x, y) in new[] { (3, 3), (14, 3), (3, 14), (14, 14) }) g.DrawRectangle(p, x, y, 7, 7);
                    break;
            }
        };
        return icon;
    }
}
