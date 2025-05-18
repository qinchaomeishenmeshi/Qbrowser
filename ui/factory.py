class UIFactory:
    @staticmethod
    def create_ui(ui_type="current"):
        """
        创建UI实例，支持新旧UI切换
        
        Args:
            ui_type: "current" (当前UI), "modern" (新UI)
        
        Returns:
            UI实例
        """
        from app import App as CurrentApp  # 当前UI
        
        if ui_type == "modern":
            # 检查是否已经开发了新UI
            try:
                from ui.modern_app import ModernApp
                return ModernApp()
            except ImportError:
                print("新UI尚未完成，使用当前UI")
                return CurrentApp()
        else:
            return CurrentApp()
