#include "Commands/UnrealMCPBlueprintNodeCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "K2Node_Event.h"
#include "K2Node_ComponentBoundEvent.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "Components/SphereComponent.h"
#include "K2Node_CallFunction.h"
#include "Components/PrimitiveComponent.h"
#include "K2Node_VariableGet.h"
#include "K2Node_InputAction.h"
#include "K2Node_Self.h"
#include "K2Node_MacroInstance.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_VariableSet.h"
#include "K2Node_SpawnActorFromClass.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "GameFramework/InputSettings.h"
#include "Camera/CameraActor.h"
#include "Kismet/GameplayStatics.h"
#include "EdGraphSchema_K2.h"

// Declare the log category
DEFINE_LOG_CATEGORY_STATIC(LogUnrealMCP, Log, All);

FUnrealMCPBlueprintNodeCommands::FUnrealMCPBlueprintNodeCommands()
{
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
    if (CommandType == TEXT("connect_blueprint_nodes"))
    {
        return HandleConnectBlueprintNodes(Params);
    }
    else if (CommandType == TEXT("add_blueprint_get_self_component_reference"))
    {
        return HandleAddBlueprintGetSelfComponentReference(Params);
    }
    else if (CommandType == TEXT("add_blueprint_event_node"))
    {
        return HandleAddBlueprintEvent(Params);
    }
    else if (CommandType == TEXT("add_blueprint_component_event"))
    {
        return HandleAddBlueprintComponentEvent(Params);
    }
    else if (CommandType == TEXT("add_blueprint_function_node"))
    {
        return HandleAddBlueprintFunctionCall(Params);
    }
    else if (CommandType == TEXT("add_blueprint_variable"))
    {
        return HandleAddBlueprintVariable(Params);
    }
    else if (CommandType == TEXT("add_blueprint_input_action_node"))
    {
        return HandleAddBlueprintInputActionNode(Params);
    }
    else if (CommandType == TEXT("add_blueprint_self_reference"))
    {
        return HandleAddBlueprintSelfReference(Params);
    }
    else if (CommandType == TEXT("find_blueprint_nodes"))
    {
        return HandleFindBlueprintNodes(Params);
    }
    else if (CommandType == TEXT("set_node_pin_default"))
    {
        return HandleSetNodePinDefault(Params);
    }
    else if (CommandType == TEXT("add_blueprint_branch"))
    {
        return HandleAddBlueprintBranch(Params);
    }
    else if (CommandType == TEXT("add_blueprint_variable_get"))
    {
        return HandleAddBlueprintVariableGet(Params);
    }
    else if (CommandType == TEXT("add_blueprint_variable_set"))
    {
        return HandleAddBlueprintVariableSet(Params);
    }
    else if (CommandType == TEXT("add_blueprint_macro"))
    {
        return HandleAddBlueprintMacro(Params);
    }
    else if (CommandType == TEXT("add_blueprint_spawn_actor_from_class"))
    {
        return HandleAddBlueprintSpawnActorFromClass(Params);
    }
    else if (CommandType == TEXT("get_node_pins"))
    {
        return HandleGetNodePins(Params);
    }
    else if (CommandType == TEXT("disconnect_pin"))
    {
        return HandleDisconnectPin(Params);
    }
    else if (CommandType == TEXT("delete_blueprint_nodes"))
    {
        return HandleDeleteBlueprintNodes(Params);
    }
    
    return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown blueprint node command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleConnectBlueprintNodes(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString SourceNodeId;
    if (!Params->TryGetStringField(TEXT("source_node_id"), SourceNodeId))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'source_node_id' parameter"));
    }

    FString TargetNodeId;
    if (!Params->TryGetStringField(TEXT("target_node_id"), TargetNodeId))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'target_node_id' parameter"));
    }

    FString SourcePinName;
    if (!Params->TryGetStringField(TEXT("source_pin"), SourcePinName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'source_pin' parameter"));
    }

    FString TargetPinName;
    if (!Params->TryGetStringField(TEXT("target_pin"), TargetPinName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'target_pin' parameter"));
    }

    // Find the blueprint
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    // Get the event graph
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get event graph"));
    }

    // Find the nodes
    UEdGraphNode* SourceNode = nullptr;
    UEdGraphNode* TargetNode = nullptr;
    for (UEdGraphNode* Node : EventGraph->Nodes)
    {
        if (Node->NodeGuid.ToString() == SourceNodeId)
        {
            SourceNode = Node;
        }
        else if (Node->NodeGuid.ToString() == TargetNodeId)
        {
            TargetNode = Node;
        }
    }

    if (!SourceNode || !TargetNode)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Source or target node not found"));
    }

    // Connect the nodes
    if (FUnrealMCPCommonUtils::ConnectGraphNodes(EventGraph, SourceNode, SourcePinName, TargetNode, TargetPinName))
    {
        // Mark the blueprint as modified
        FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

        TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
        ResultObj->SetStringField(TEXT("source_node_id"), SourceNodeId);
        ResultObj->SetStringField(TEXT("target_node_id"), TargetNodeId);
        return ResultObj;
    }

    return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to connect nodes"));
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintGetSelfComponentReference(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString ComponentName;
    if (!Params->TryGetStringField(TEXT("component_name"), ComponentName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'component_name' parameter"));
    }

    // Get position parameters (optional)
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }

    // Find the blueprint
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    // Get the event graph
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get event graph"));
    }
    
    // We'll skip component verification since the GetAllNodes API may have changed in UE5.5
    
    // Create the variable get node directly
    UK2Node_VariableGet* GetComponentNode = NewObject<UK2Node_VariableGet>(EventGraph);
    if (!GetComponentNode)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create get component node"));
    }
    
    // Set up the variable reference properly for UE5.5
    FMemberReference& VarRef = GetComponentNode->VariableReference;
    VarRef.SetSelfMember(FName(*ComponentName));
    
    // Set node position
    GetComponentNode->NodePosX = NodePosition.X;
    GetComponentNode->NodePosY = NodePosition.Y;
    
    // Add to graph
    EventGraph->AddNode(GetComponentNode);
    GetComponentNode->CreateNewGuid();
    GetComponentNode->PostPlacedNewNode();
    GetComponentNode->AllocateDefaultPins();
    
    // Explicitly reconstruct node for UE5.5
    GetComponentNode->ReconstructNode();
    
    // Mark the blueprint as modified
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("node_id"), GetComponentNode->NodeGuid.ToString());
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintEvent(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString EventName;
    if (!Params->TryGetStringField(TEXT("event_name"), EventName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'event_name' parameter"));
    }

    // Get position parameters (optional)
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }

    // Find the blueprint
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    // Get the event graph
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get event graph"));
    }

    // Create the event node
    UK2Node_Event* EventNode = FUnrealMCPCommonUtils::CreateEventNode(EventGraph, EventName, NodePosition);
    if (!EventNode)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create event node"));
    }

    // Mark the blueprint as modified
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("node_id"), EventNode->NodeGuid.ToString());
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintComponentEvent(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString ComponentName;
    if (!Params->TryGetStringField(TEXT("component_name"), ComponentName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'component_name' parameter"));
    }

    FString EventName = TEXT("OnComponentBeginOverlap");
    Params->TryGetStringField(TEXT("event_name"), EventName);

    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }

    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get event graph"));
    }

    // Verify component exists on the Blueprint SCS
    bool bFoundComponent = false;
    if (Blueprint->SimpleConstructionScript)
    {
        for (USCS_Node* Node : Blueprint->SimpleConstructionScript->GetAllNodes())
        {
            if (Node && Node->GetVariableName().ToString() == ComponentName)
            {
                bFoundComponent = true;
                break;
            }
        }
    }
    if (!bFoundComponent)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Component not found on Blueprint: %s"), *ComponentName));
    }

    UK2Node_ComponentBoundEvent* BoundEvent = NewObject<UK2Node_ComponentBoundEvent>(EventGraph);
    BoundEvent->CreateNewGuid();
    BoundEvent->PostPlacedNewNode();

    FMulticastDelegateProperty* DelegateProp = FindFProperty<FMulticastDelegateProperty>(
        UPrimitiveComponent::StaticClass(), FName(*EventName));
    if (!DelegateProp)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Delegate not found: %s"), *EventName));
    }

    UClass* BPClass = Blueprint->SkeletonGeneratedClass
        ? Blueprint->SkeletonGeneratedClass
        : Blueprint->GeneratedClass;
    FObjectProperty* ComponentProp = BPClass
        ? FindFProperty<FObjectProperty>(BPClass, FName(*ComponentName))
        : nullptr;

    if (ComponentProp)
    {
        BoundEvent->InitializeComponentBoundEventParams(ComponentProp, DelegateProp);
    }
    else
    {
        // Fallback when skeleton var is not ready yet
        BoundEvent->ComponentPropertyName = FName(*ComponentName);
        BoundEvent->DelegatePropertyName = DelegateProp->GetFName();
        BoundEvent->DelegateOwnerClass = UPrimitiveComponent::StaticClass();
        BoundEvent->EventReference.SetExternalMember(DelegateProp->GetFName(), UPrimitiveComponent::StaticClass());
        BoundEvent->bInternalEvent = true;
        BoundEvent->CustomFunctionName = FName(*FString::Printf(
            TEXT("BndEvt__%s_%s_%s"), *BlueprintName, *ComponentName, *EventName));
    }

    BoundEvent->AllocateDefaultPins();
    BoundEvent->NodePosX = NodePosition.X;
    BoundEvent->NodePosY = NodePosition.Y;
    EventGraph->AddNode(BoundEvent, false, false);

    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("node_id"), BoundEvent->NodeGuid.ToString());
    ResultObj->SetStringField(TEXT("component_name"), ComponentName);
    ResultObj->SetStringField(TEXT("event_name"), EventName);
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintFunctionCall(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString FunctionName;
    if (!Params->TryGetStringField(TEXT("function_name"), FunctionName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'function_name' parameter"));
    }

    // Get position parameters (optional)
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }

    // Check for target parameter (optional)
    FString Target;
    Params->TryGetStringField(TEXT("target"), Target);

    // Find the blueprint
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    // Get the event graph
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get event graph"));
    }

    // Find the function
    UFunction* Function = nullptr;
    UK2Node_CallFunction* FunctionNode = nullptr;
    
    // Add extensive logging for debugging
    UE_LOG(LogTemp, Display, TEXT("Looking for function '%s' in target '%s'"), 
           *FunctionName, Target.IsEmpty() ? TEXT("Blueprint") : *Target);
    
    // Check if we have a target class specified
    if (!Target.IsEmpty())
    {
        // Try to find the target class
        UClass* TargetClass = nullptr;
        
        // First try without a prefix
        TargetClass = FindObject<UClass>(ANY_PACKAGE, *Target);
        UE_LOG(LogTemp, Display, TEXT("Tried to find class '%s': %s"), 
               *Target, TargetClass ? TEXT("Found") : TEXT("Not found"));
        
        // If not found, try with U prefix (common convention for UE classes)
        if (!TargetClass && !Target.StartsWith(TEXT("U")))
        {
            FString TargetWithPrefix = FString(TEXT("U")) + Target;
            TargetClass = FindObject<UClass>(ANY_PACKAGE, *TargetWithPrefix);
            UE_LOG(LogTemp, Display, TEXT("Tried to find class '%s': %s"), 
                   *TargetWithPrefix, TargetClass ? TEXT("Found") : TEXT("Not found"));
        }
        
        // If still not found, try with common component names
        if (!TargetClass)
        {
            // Try some common component class names
            TArray<FString> PossibleClassNames;
            PossibleClassNames.Add(FString(TEXT("U")) + Target + TEXT("Component"));
            PossibleClassNames.Add(Target + TEXT("Component"));
            
            for (const FString& ClassName : PossibleClassNames)
            {
                TargetClass = FindObject<UClass>(ANY_PACKAGE, *ClassName);
                if (TargetClass)
                {
                    UE_LOG(LogTemp, Display, TEXT("Found class using alternative name '%s'"), *ClassName);
                    break;
                }
            }
        }
        
        // Special case handling for common classes like UGameplayStatics
        if (!TargetClass && (Target == TEXT("UGameplayStatics") || Target == TEXT("GameplayStatics")))
        {
            // For UGameplayStatics, use a direct reference to known class
            TargetClass = FindObject<UClass>(ANY_PACKAGE, TEXT("UGameplayStatics"));
            if (!TargetClass)
            {
                // Try loading it from its known package
                TargetClass = LoadObject<UClass>(nullptr, TEXT("/Script/Engine.GameplayStatics"));
                UE_LOG(LogTemp, Display, TEXT("Explicitly loading GameplayStatics: %s"), 
                       TargetClass ? TEXT("Success") : TEXT("Failed"));
            }
        }

        if (!TargetClass && (Target == TEXT("UKismetMathLibrary") || Target == TEXT("KismetMathLibrary")))
        {
            TargetClass = FindObject<UClass>(ANY_PACKAGE, TEXT("UKismetMathLibrary"));
            if (!TargetClass)
            {
                TargetClass = LoadObject<UClass>(nullptr, TEXT("/Script/Engine.KismetMathLibrary"));
                UE_LOG(LogTemp, Display, TEXT("Explicitly loading KismetMathLibrary: %s"),
                       TargetClass ? TEXT("Success") : TEXT("Failed"));
            }
        }

        if (!TargetClass && (Target == TEXT("UKismetArrayLibrary") || Target == TEXT("KismetArrayLibrary")))
        {
            TargetClass = FindObject<UClass>(ANY_PACKAGE, TEXT("UKismetArrayLibrary"));
            if (!TargetClass)
            {
                TargetClass = LoadObject<UClass>(nullptr, TEXT("/Script/Engine.KismetArrayLibrary"));
            }
        }

        if (!TargetClass && (Target == TEXT("UKismetSystemLibrary") || Target == TEXT("KismetSystemLibrary")))
        {
            TargetClass = FindObject<UClass>(ANY_PACKAGE, TEXT("UKismetSystemLibrary"));
            if (!TargetClass)
            {
                TargetClass = LoadObject<UClass>(nullptr, TEXT("/Script/Engine.KismetSystemLibrary"));
            }
        }
        
        // If we found a target class, look for the function there
        if (TargetClass)
        {
            UE_LOG(LogTemp, Display, TEXT("Looking for function '%s' in class '%s'"), 
                   *FunctionName, *TargetClass->GetName());
                   
            // First try exact name
            Function = TargetClass->FindFunctionByName(*FunctionName);
            
            // If not found, try class hierarchy
            UClass* CurrentClass = TargetClass;
            while (!Function && CurrentClass)
            {
                UE_LOG(LogTemp, Display, TEXT("Searching in class: %s"), *CurrentClass->GetName());
                
                // Try exact match
                Function = CurrentClass->FindFunctionByName(*FunctionName);
                
                // Try case-insensitive match
                if (!Function)
                {
                    for (TFieldIterator<UFunction> FuncIt(CurrentClass); FuncIt; ++FuncIt)
                    {
                        UFunction* AvailableFunc = *FuncIt;
                        UE_LOG(LogTemp, Display, TEXT("  - Available function: %s"), *AvailableFunc->GetName());
                        
                        if (AvailableFunc->GetName().Equals(FunctionName, ESearchCase::IgnoreCase))
                        {
                            UE_LOG(LogTemp, Display, TEXT("  - Found case-insensitive match: %s"), *AvailableFunc->GetName());
                            Function = AvailableFunc;
                            break;
                        }
                    }
                }
                
                // Move to parent class
                CurrentClass = CurrentClass->GetSuperClass();
            }
            
            // Special handling for known functions
            if (!Function)
            {
                if (TargetClass->GetName() == TEXT("GameplayStatics") && 
                    (FunctionName == TEXT("GetActorOfClass") || FunctionName.Equals(TEXT("GetActorOfClass"), ESearchCase::IgnoreCase)))
                {
                    UE_LOG(LogTemp, Display, TEXT("Using special case handling for GameplayStatics::GetActorOfClass"));
                    
                    // Create the function node directly
                    FunctionNode = NewObject<UK2Node_CallFunction>(EventGraph);
                    if (FunctionNode)
                    {
                        // Direct setup for known function
                        FunctionNode->FunctionReference.SetExternalMember(
                            FName(TEXT("GetActorOfClass")), 
                            TargetClass
                        );
                        
                        FunctionNode->NodePosX = NodePosition.X;
                        FunctionNode->NodePosY = NodePosition.Y;
                        EventGraph->AddNode(FunctionNode);
                        FunctionNode->CreateNewGuid();
                        FunctionNode->PostPlacedNewNode();
                        FunctionNode->AllocateDefaultPins();
                        
                        UE_LOG(LogTemp, Display, TEXT("Created GetActorOfClass node directly"));
                        
                        // List all pins
                        for (UEdGraphPin* Pin : FunctionNode->Pins)
                        {
                            UE_LOG(LogTemp, Display, TEXT("  - Pin: %s, Direction: %d, Category: %s"), 
                                   *Pin->PinName.ToString(), (int32)Pin->Direction, *Pin->PinType.PinCategory.ToString());
                        }
                    }
                }
            }
        }
    }
    
    // If we still haven't found the function, try in the blueprint's class
    if (!Function && !FunctionNode)
    {
        UE_LOG(LogTemp, Display, TEXT("Trying to find function in blueprint class"));
        Function = Blueprint->GeneratedClass->FindFunctionByName(*FunctionName);
    }
    
    // Create the function call node if we found the function
    if (Function && !FunctionNode)
    {
        FunctionNode = FUnrealMCPCommonUtils::CreateFunctionCallNode(EventGraph, Function, NodePosition);
    }
    
    if (!FunctionNode)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Function not found: %s in target %s"), *FunctionName, Target.IsEmpty() ? TEXT("Blueprint") : *Target));
    }

    // Set parameters if provided
    if (Params->HasField(TEXT("params")))
    {
        const TSharedPtr<FJsonObject>* ParamsObj;
        if (Params->TryGetObjectField(TEXT("params"), ParamsObj))
        {
            // Process parameters
            for (const TPair<FString, TSharedPtr<FJsonValue>>& Param : (*ParamsObj)->Values)
            {
                const FString& ParamName = Param.Key;
                const TSharedPtr<FJsonValue>& ParamValue = Param.Value;
                
                // Find the parameter pin
                UEdGraphPin* ParamPin = FUnrealMCPCommonUtils::FindPin(FunctionNode, ParamName, EGPD_Input);
                if (ParamPin)
                {
                    UE_LOG(LogTemp, Display, TEXT("Found parameter pin '%s' of category '%s'"), 
                           *ParamName, *ParamPin->PinType.PinCategory.ToString());
                    UE_LOG(LogTemp, Display, TEXT("  Current default value: '%s'"), *ParamPin->DefaultValue);
                    if (ParamPin->PinType.PinSubCategoryObject.IsValid())
                    {
                        UE_LOG(LogTemp, Display, TEXT("  Pin subcategory: '%s'"), 
                               *ParamPin->PinType.PinSubCategoryObject->GetName());
                    }
                    
                    // Set parameter based on type
                    if (ParamValue->Type == EJson::String)
                    {
                        FString StringVal = ParamValue->AsString();
                        UE_LOG(LogTemp, Display, TEXT("  Setting string parameter '%s' to: '%s'"), 
                               *ParamName, *StringVal);
                        
                        // Handle class reference parameters (e.g., ActorClass in GetActorOfClass)
                        if (ParamPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Class)
                        {
                            // For class references, we require the exact class name with proper prefix
                            // - Actor classes must start with 'A' (e.g., ACameraActor)
                            // - Non-actor classes must start with 'U' (e.g., UObject)
                            const FString& ClassName = StringVal;
                            
                            // TODO: This likely won't work in UE5.5+, so don't rely on it.
                            UClass* Class = FindObject<UClass>(ANY_PACKAGE, *ClassName);

                            if (!Class)
                            {
                                Class = LoadObject<UClass>(nullptr, *ClassName);
                                UE_LOG(LogUnrealMCP, Display, TEXT("FindObject<UClass> failed. Assuming soft path  path: %s"), *ClassName);
                            }
                            
                            // If not found, try with Engine module path
                            if (!Class)
                            {
                                FString EngineClassName = FString::Printf(TEXT("/Script/Engine.%s"), *ClassName);
                                Class = LoadObject<UClass>(nullptr, *EngineClassName);
                                UE_LOG(LogUnrealMCP, Display, TEXT("Trying Engine module path: %s"), *EngineClassName);
                            }
                            
                            if (!Class)
                            {
                                UE_LOG(LogUnrealMCP, Error, TEXT("Failed to find class '%s'. Make sure to use the exact class name with proper prefix (A for actors, U for non-actors)"), *ClassName);
                                return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to find class '%s'"), *ClassName));
                            }

                            const UEdGraphSchema_K2* K2Schema = Cast<const UEdGraphSchema_K2>(EventGraph->GetSchema());
                            if (!K2Schema)
                            {
                                UE_LOG(LogUnrealMCP, Error, TEXT("Failed to get K2Schema"));
                                return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get K2Schema"));
                            }

                            K2Schema->TrySetDefaultObject(*ParamPin, Class);
                            if (ParamPin->DefaultObject != Class)
                            {
                                UE_LOG(LogUnrealMCP, Error, TEXT("Failed to set class reference for pin '%s' to '%s'"), *ParamPin->PinName.ToString(), *ClassName);
                                return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to set class reference for pin '%s'"), *ParamPin->PinName.ToString()));
                            }

                            UE_LOG(LogUnrealMCP, Log, TEXT("Successfully set class reference for pin '%s' to '%s'"), *ParamPin->PinName.ToString(), *ClassName);
                            continue;
                        }
                        else if (ParamPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Int)
                        {
                            // Ensure we're using an integer value (no decimal)
                            int32 IntValue = FMath::RoundToInt(ParamValue->AsNumber());
                            ParamPin->DefaultValue = FString::FromInt(IntValue);
                            UE_LOG(LogTemp, Display, TEXT("  Set integer parameter '%s' to: %d (string: '%s')"), 
                                   *ParamName, IntValue, *ParamPin->DefaultValue);
                        }
                        else if (ParamPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Float)
                        {
                            // For other numeric types
                            float FloatValue = ParamValue->AsNumber();
                            ParamPin->DefaultValue = FString::SanitizeFloat(FloatValue);
                            UE_LOG(LogTemp, Display, TEXT("  Set float parameter '%s' to: %f (string: '%s')"), 
                                   *ParamName, FloatValue, *ParamPin->DefaultValue);
                        }
                        else if (ParamPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Boolean)
                        {
                            bool BoolValue = ParamValue->AsBool();
                            ParamPin->DefaultValue = BoolValue ? TEXT("true") : TEXT("false");
                            UE_LOG(LogTemp, Display, TEXT("  Set boolean parameter '%s' to: %s"), 
                                   *ParamName, *ParamPin->DefaultValue);
                        }
                        else if (ParamPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Struct && ParamPin->PinType.PinSubCategoryObject == TBaseStructure<FVector>::Get())
                        {
                            // Handle array parameters - like Vector parameters
                            const TArray<TSharedPtr<FJsonValue>>* ArrayValue;
                            if (ParamValue->TryGetArray(ArrayValue))
                            {
                                // Check if this could be a vector (array of 3 numbers)
                                if (ArrayValue->Num() == 3)
                                {
                                    // Create a proper vector string: (X=0.0,Y=0.0,Z=1000.0)
                                    float X = (*ArrayValue)[0]->AsNumber();
                                    float Y = (*ArrayValue)[1]->AsNumber();
                                    float Z = (*ArrayValue)[2]->AsNumber();
                                    
                                    FString VectorString = FString::Printf(TEXT("(X=%f,Y=%f,Z=%f)"), X, Y, Z);
                                    ParamPin->DefaultValue = VectorString;
                                    
                                    UE_LOG(LogTemp, Display, TEXT("  Set vector parameter '%s' to: %s"), 
                                           *ParamName, *VectorString);
                                    UE_LOG(LogTemp, Display, TEXT("  Final pin value: '%s'"), 
                                           *ParamPin->DefaultValue);
                                }
                                else
                                {
                                    UE_LOG(LogTemp, Warning, TEXT("Array parameter type not fully supported yet"));
                                }
                            }
                        }
                    }
                    else if (ParamValue->Type == EJson::Number)
                    {
                        // Handle integer vs float parameters correctly
                        if (ParamPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Int)
                        {
                            // Ensure we're using an integer value (no decimal)
                            int32 IntValue = FMath::RoundToInt(ParamValue->AsNumber());
                            ParamPin->DefaultValue = FString::FromInt(IntValue);
                            UE_LOG(LogTemp, Display, TEXT("  Set integer parameter '%s' to: %d (string: '%s')"), 
                                   *ParamName, IntValue, *ParamPin->DefaultValue);
                        }
                        else
                        {
                            // For other numeric types
                            float FloatValue = ParamValue->AsNumber();
                            ParamPin->DefaultValue = FString::SanitizeFloat(FloatValue);
                            UE_LOG(LogTemp, Display, TEXT("  Set float parameter '%s' to: %f (string: '%s')"), 
                                   *ParamName, FloatValue, *ParamPin->DefaultValue);
                        }
                    }
                    else if (ParamValue->Type == EJson::Boolean)
                    {
                        bool BoolValue = ParamValue->AsBool();
                        ParamPin->DefaultValue = BoolValue ? TEXT("true") : TEXT("false");
                        UE_LOG(LogTemp, Display, TEXT("  Set boolean parameter '%s' to: %s"), 
                               *ParamName, *ParamPin->DefaultValue);
                    }
                    else if (ParamValue->Type == EJson::Array)
                    {
                        UE_LOG(LogTemp, Display, TEXT("  Processing array parameter '%s'"), *ParamName);
                        // Handle array parameters - like Vector parameters
                        const TArray<TSharedPtr<FJsonValue>>* ArrayValue;
                        if (ParamValue->TryGetArray(ArrayValue))
                        {
                            // Check if this could be a vector (array of 3 numbers)
                            if (ArrayValue->Num() == 3 && 
                                (ParamPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Struct) &&
                                (ParamPin->PinType.PinSubCategoryObject == TBaseStructure<FVector>::Get()))
                            {
                                // Create a proper vector string: (X=0.0,Y=0.0,Z=1000.0)
                                float X = (*ArrayValue)[0]->AsNumber();
                                float Y = (*ArrayValue)[1]->AsNumber();
                                float Z = (*ArrayValue)[2]->AsNumber();
                                
                                FString VectorString = FString::Printf(TEXT("(X=%f,Y=%f,Z=%f)"), X, Y, Z);
                                ParamPin->DefaultValue = VectorString;
                                
                                UE_LOG(LogTemp, Display, TEXT("  Set vector parameter '%s' to: %s"), 
                                       *ParamName, *VectorString);
                                UE_LOG(LogTemp, Display, TEXT("  Final pin value: '%s'"), 
                                       *ParamPin->DefaultValue);
                            }
                            else
                            {
                                UE_LOG(LogTemp, Warning, TEXT("Array parameter type not fully supported yet"));
                            }
                        }
                    }
                    // Add handling for other types as needed
                }
                else
                {
                    UE_LOG(LogTemp, Warning, TEXT("Parameter pin '%s' not found"), *ParamName);
                }
            }
        }
    }

    // Mark the blueprint as modified
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("node_id"), FunctionNode->NodeGuid.ToString());
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintVariable(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString VariableName;
    if (!Params->TryGetStringField(TEXT("variable_name"), VariableName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'variable_name' parameter"));
    }

    FString VariableType;
    if (!Params->TryGetStringField(TEXT("variable_type"), VariableType))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'variable_type' parameter"));
    }

    // Get optional parameters
    bool IsExposed = false;
    if (Params->HasField(TEXT("is_exposed")))
    {
        IsExposed = Params->GetBoolField(TEXT("is_exposed"));
    }

    // Find the blueprint
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    // Create variable based on type
    FEdGraphPinType PinType;
    
    // Set up pin type based on variable_type string
    if (VariableType == TEXT("Boolean"))
    {
        PinType.PinCategory = UEdGraphSchema_K2::PC_Boolean;
    }
    else if (VariableType == TEXT("Integer") || VariableType == TEXT("Int"))
    {
        PinType.PinCategory = UEdGraphSchema_K2::PC_Int;
    }
    else if (VariableType == TEXT("Float") || VariableType == TEXT("Real") || VariableType == TEXT("Double"))
    {
        PinType.PinCategory = UEdGraphSchema_K2::PC_Real;
        PinType.PinSubCategory = UEdGraphSchema_K2::PC_Double;
    }
    else if (VariableType == TEXT("String"))
    {
        PinType.PinCategory = UEdGraphSchema_K2::PC_String;
    }
    else if (VariableType == TEXT("Vector"))
    {
        PinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
        PinType.PinSubCategoryObject = TBaseStructure<FVector>::Get();
    }
    else if (VariableType == TEXT("VectorArray") || VariableType == TEXT("Array<Vector>") || VariableType == TEXT("Vector[]"))
    {
        PinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
        PinType.PinSubCategoryObject = TBaseStructure<FVector>::Get();
        PinType.ContainerType = EPinContainerType::Array;
    }
    else
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unsupported variable type: %s"), *VariableType));
    }

    // Create the variable
    FBlueprintEditorUtils::AddMemberVariable(Blueprint, FName(*VariableName), PinType);

    // Set variable properties
    FBPVariableDescription* NewVar = nullptr;
    for (FBPVariableDescription& Variable : Blueprint->NewVariables)
    {
        if (Variable.VarName == FName(*VariableName))
        {
            NewVar = &Variable;
            break;
        }
    }

    if (NewVar)
    {
        // Set exposure in editor
        if (IsExposed)
        {
            NewVar->PropertyFlags |= CPF_Edit;
        }
        FString DefaultValue;
        if (Params->TryGetStringField(TEXT("default_value"), DefaultValue))
        {
            NewVar->DefaultValue = DefaultValue;
        }
    }

    // Mark the blueprint as modified
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("variable_name"), VariableName);
    ResultObj->SetStringField(TEXT("variable_type"), VariableType);
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintInputActionNode(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString ActionName;
    if (!Params->TryGetStringField(TEXT("action_name"), ActionName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'action_name' parameter"));
    }

    // Get position parameters (optional)
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }

    // Find the blueprint
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    // Get the event graph
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get event graph"));
    }

    // Create the input action node
    UK2Node_InputAction* InputActionNode = FUnrealMCPCommonUtils::CreateInputActionNode(EventGraph, ActionName, NodePosition);
    if (!InputActionNode)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create input action node"));
    }

    // Mark the blueprint as modified
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("node_id"), InputActionNode->NodeGuid.ToString());
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintSelfReference(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    // Get position parameters (optional)
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }

    // Find the blueprint
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    // Get the event graph
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get event graph"));
    }

    // Create the self node
    UK2Node_Self* SelfNode = FUnrealMCPCommonUtils::CreateSelfReferenceNode(EventGraph, NodePosition);
    if (!SelfNode)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create self node"));
    }

    // Mark the blueprint as modified
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("node_id"), SelfNode->NodeGuid.ToString());
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleFindBlueprintNodes(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString NodeType;
    if (!Params->TryGetStringField(TEXT("node_type"), NodeType))
    {
        // Default to listing all useful nodes when omitted
        NodeType = TEXT("All");
    }

    // Find the blueprint
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    // Get the event graph
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get event graph"));
    }

    // Create a JSON array for the node GUIDs / details
    TArray<TSharedPtr<FJsonValue>> NodeGuidArray;
    TArray<TSharedPtr<FJsonValue>> NodeDetailArray;
    
    // Filter nodes by the exact requested type
    if (NodeType == TEXT("Event"))
    {
        FString EventName;
        if (!Params->TryGetStringField(TEXT("event_name"), EventName))
        {
            // Accept event_type as an alias used by the Python MCP tools
            Params->TryGetStringField(TEXT("event_type"), EventName);
        }
        if (EventName.IsEmpty())
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'event_name' parameter for Event node search"));
        }
        
        // Look for nodes with exact event name (e.g., ReceiveBeginPlay)
        for (UEdGraphNode* Node : EventGraph->Nodes)
        {
            UK2Node_Event* EventNode = Cast<UK2Node_Event>(Node);
            if (EventNode && EventNode->EventReference.GetMemberName() == FName(*EventName))
            {
                UE_LOG(LogTemp, Display, TEXT("Found event node with name %s: %s"), *EventName, *EventNode->NodeGuid.ToString());
                NodeGuidArray.Add(MakeShared<FJsonValueString>(EventNode->NodeGuid.ToString()));
            }
        }
    }
    else if (NodeType == TEXT("Function") || NodeType == TEXT("All") || NodeType == TEXT("CallFunction"))
    {
        FString FunctionFilter;
        Params->TryGetStringField(TEXT("function_name"), FunctionFilter);
        if (FunctionFilter.IsEmpty())
        {
            Params->TryGetStringField(TEXT("event_name"), FunctionFilter);
        }

        for (UEdGraphNode* Node : EventGraph->Nodes)
        {
            if (!Node)
            {
                continue;
            }

            FString Title = Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString();
            FString ClassName = Node->GetClass()->GetName();
            FString FuncName;
            UK2Node_CallFunction* CallNode = Cast<UK2Node_CallFunction>(Node);
            UK2Node_MacroInstance* MacroNode = Cast<UK2Node_MacroInstance>(Node);

            if (CallNode)
            {
                FuncName = CallNode->FunctionReference.GetMemberName().ToString();
            }
            else if (MacroNode)
            {
                if (UEdGraph* MacroGraph = MacroNode->GetMacroGraph())
                {
                    FuncName = MacroGraph->GetName();
                }
            }

            const bool bMatchesFilter =
                FunctionFilter.IsEmpty() ||
                FuncName.Contains(FunctionFilter) ||
                Title.Contains(FunctionFilter) ||
                ClassName.Contains(FunctionFilter);

            // For Function searches without filter, include call nodes; for All include everything
            bool bShouldAdd = false;
            if (NodeType == TEXT("All"))
            {
                bShouldAdd = true;
            }
            else if ((NodeType == TEXT("Function") || NodeType == TEXT("CallFunction")) && bMatchesFilter)
            {
                bShouldAdd = (CallNode != nullptr) || (MacroNode != nullptr) || Title.Contains(FunctionFilter);
            }

            if (bShouldAdd)
            {
                NodeGuidArray.Add(MakeShared<FJsonValueString>(Node->NodeGuid.ToString()));

                TSharedPtr<FJsonObject> Detail = MakeShared<FJsonObject>();
                Detail->SetStringField(TEXT("node_guid"), Node->NodeGuid.ToString());
                Detail->SetStringField(TEXT("class"), ClassName);
                Detail->SetStringField(TEXT("title"), Title);
                Detail->SetStringField(TEXT("function_name"), FuncName);
                Detail->SetNumberField(TEXT("pos_x"), Node->NodePosX);
                Detail->SetNumberField(TEXT("pos_y"), Node->NodePosY);
                NodeDetailArray.Add(MakeShared<FJsonValueObject>(Detail));
            }
        }
    }
    
    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetBoolField(TEXT("success"), true);
    ResultObj->SetArrayField(TEXT("node_guids"), NodeGuidArray);
    if (NodeDetailArray.Num() > 0)
    {
        ResultObj->SetArrayField(TEXT("nodes"), NodeDetailArray);
    }
    
    return ResultObj;
} TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleSetNodePinDefault(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString NodeId;
    if (!Params->TryGetStringField(TEXT("node_id"), NodeId))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'node_id' parameter"));
    }

    FString PinName;
    if (!Params->TryGetStringField(TEXT("pin_name"), PinName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'pin_name' parameter"));
    }

    FString DefaultValue;
    if (!Params->TryGetStringField(TEXT("default_value"), DefaultValue))
    {
        // Also accept numeric default_value
        double NumberValue = 0.0;
        if (Params->TryGetNumberField(TEXT("default_value"), NumberValue))
        {
            DefaultValue = FString::SanitizeFloat(NumberValue);
        }
        else
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'default_value' parameter"));
        }
    }

    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get event graph"));
    }

    FGuid NodeGuid;
    if (!FGuid::Parse(NodeId, NodeGuid))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Invalid node_id GUID"));
    }

    UEdGraphNode* TargetNode = nullptr;
    for (UEdGraphNode* Node : EventGraph->Nodes)
    {
        if (Node && Node->NodeGuid == NodeGuid)
        {
            TargetNode = Node;
            break;
        }
    }
    if (!TargetNode)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Node not found"));
    }

    UEdGraphPin* TargetPin = nullptr;
    for (UEdGraphPin* Pin : TargetNode->Pins)
    {
        if (Pin && Pin->PinName.ToString().Equals(PinName, ESearchCase::IgnoreCase))
        {
            TargetPin = Pin;
            break;
        }
    }
    if (!TargetPin)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Pin not found: %s"), *PinName));
    }

    const UEdGraphSchema_K2* K2Schema = Cast<const UEdGraphSchema_K2>(EventGraph->GetSchema());
    if (K2Schema)
    {
        K2Schema->TrySetDefaultValue(*TargetPin, DefaultValue);
    }
    else
    {
        TargetPin->DefaultValue = DefaultValue;
    }

    TargetNode->PinDefaultValueChanged(TargetPin);
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetBoolField(TEXT("success"), true);
    ResultObj->SetStringField(TEXT("node_id"), NodeId);
    ResultObj->SetStringField(TEXT("pin_name"), PinName);
    ResultObj->SetStringField(TEXT("default_value"), TargetPin->DefaultValue);
    return ResultObj;
}
TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintBranch(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing blueprint_name"));
    }
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint not found"));
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No event graph"));

    UK2Node_IfThenElse* Branch = NewObject<UK2Node_IfThenElse>(EventGraph);
    Branch->NodePosX = NodePosition.X;
    Branch->NodePosY = NodePosition.Y;
    EventGraph->AddNode(Branch, true, false);
    Branch->CreateNewGuid();
    Branch->PostPlacedNewNode();
    Branch->AllocateDefaultPins();
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), true);
    Result->SetStringField(TEXT("node_id"), Branch->NodeGuid.ToString());
    return Result;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintVariableGet(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName, VariableName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName) || !Params->TryGetStringField(TEXT("variable_name"), VariableName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing blueprint_name or variable_name"));
    }
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint not found"));
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No event graph"));

    UK2Node_VariableGet* Node = NewObject<UK2Node_VariableGet>(EventGraph);
    Node->VariableReference.SetSelfMember(FName(*VariableName));
    Node->NodePosX = NodePosition.X;
    Node->NodePosY = NodePosition.Y;
    EventGraph->AddNode(Node, true, false);
    Node->CreateNewGuid();
    Node->AllocateDefaultPins();
    Node->ReconstructNode();
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), true);
    Result->SetStringField(TEXT("node_id"), Node->NodeGuid.ToString());
    return Result;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintVariableSet(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName, VariableName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName) || !Params->TryGetStringField(TEXT("variable_name"), VariableName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing blueprint_name or variable_name"));
    }
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint not found"));
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No event graph"));

    UK2Node_VariableSet* Node = NewObject<UK2Node_VariableSet>(EventGraph);
    Node->VariableReference.SetSelfMember(FName(*VariableName));
    Node->NodePosX = NodePosition.X;
    Node->NodePosY = NodePosition.Y;
    EventGraph->AddNode(Node, true, false);
    Node->CreateNewGuid();
    Node->AllocateDefaultPins();
    Node->ReconstructNode();

    FString DefaultValue;
    if (Params->TryGetStringField(TEXT("default_value"), DefaultValue))
    {
        if (UEdGraphPin* ValuePin = Node->FindPin(FName(*VariableName)))
        {
            const UEdGraphSchema_K2* Schema = Cast<const UEdGraphSchema_K2>(EventGraph->GetSchema());
            if (Schema) Schema->TrySetDefaultValue(*ValuePin, DefaultValue);
            else ValuePin->DefaultValue = DefaultValue;
        }
        else if (UEdGraphPin* ValuePin2 = Node->FindPin(TEXT("DefaultValue")))
        {
            ValuePin2->DefaultValue = DefaultValue;
        }
        else
        {
            for (UEdGraphPin* Pin : Node->Pins)
            {
                if (Pin && Pin->Direction == EGPD_Input && Pin->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec && Pin->PinName != UEdGraphSchema_K2::PN_Self)
                {
                    const UEdGraphSchema_K2* Schema = Cast<const UEdGraphSchema_K2>(EventGraph->GetSchema());
                    if (Schema) Schema->TrySetDefaultValue(*Pin, DefaultValue);
                    else Pin->DefaultValue = DefaultValue;
                    break;
                }
            }
        }
    }

    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), true);
    Result->SetStringField(TEXT("node_id"), Node->NodeGuid.ToString());
    return Result;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintMacro(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName, MacroName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName) || !Params->TryGetStringField(TEXT("macro_name"), MacroName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing blueprint_name or macro_name"));
    }
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint not found"));
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No event graph"));

    UBlueprint* MacroLib = LoadObject<UBlueprint>(nullptr, TEXT("/Engine/EditorBlueprintResources/StandardMacros.StandardMacros"));
    if (!MacroLib) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("StandardMacros not found"));

    UEdGraph* MacroGraph = nullptr;
    for (UEdGraph* Graph : MacroLib->MacroGraphs)
    {
        if (Graph && Graph->GetName().Equals(MacroName, ESearchCase::IgnoreCase))
        {
            MacroGraph = Graph;
            break;
        }
    }
    if (!MacroGraph)
    {
        // Accept common aliases
        FString Wanted = MacroName;
        if (Wanted.Equals(TEXT("For Each Loop"), ESearchCase::IgnoreCase)) Wanted = TEXT("ForEachLoop");
        if (Wanted.Equals(TEXT("For Loop"), ESearchCase::IgnoreCase)) Wanted = TEXT("ForLoop");
        for (UEdGraph* Graph : MacroLib->MacroGraphs)
        {
            if (Graph && Graph->GetName().Equals(Wanted, ESearchCase::IgnoreCase))
            {
                MacroGraph = Graph;
                break;
            }
        }
    }
    if (!MacroGraph) return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Macro not found: %s"), *MacroName));

    UK2Node_MacroInstance* Node = NewObject<UK2Node_MacroInstance>(EventGraph);
    Node->SetMacroGraph(MacroGraph);
    Node->NodePosX = NodePosition.X;
    Node->NodePosY = NodePosition.Y;
    EventGraph->AddNode(Node, true, false);
    Node->CreateNewGuid();
    Node->AllocateDefaultPins();
    Node->ReconstructNode();
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), true);
    Result->SetStringField(TEXT("node_id"), Node->NodeGuid.ToString());
    Result->SetStringField(TEXT("macro_name"), MacroGraph->GetName());
    return Result;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleAddBlueprintSpawnActorFromClass(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing blueprint_name"));
    }
    FString ActorClassPath;
    Params->TryGetStringField(TEXT("actor_class"), ActorClassPath);
    FVector2D NodePosition(0.0f, 0.0f);
    if (Params->HasField(TEXT("node_position")))
    {
        NodePosition = FUnrealMCPCommonUtils::GetVector2DFromJson(Params, TEXT("node_position"));
    }
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint not found"));
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No event graph"));

    UK2Node_SpawnActorFromClass* Node = NewObject<UK2Node_SpawnActorFromClass>(EventGraph);
    Node->NodePosX = NodePosition.X;
    Node->NodePosY = NodePosition.Y;
    EventGraph->AddNode(Node, true, false);
    Node->CreateNewGuid();
    Node->AllocateDefaultPins();
    Node->ReconstructNode();

    if (!ActorClassPath.IsEmpty())
    {
        UClass* ActorClass = LoadObject<UClass>(nullptr, *ActorClassPath);
        if (!ActorClass)
        {
            // Try generated class from blueprint asset path
            if (UBlueprint* ClassBP = LoadObject<UBlueprint>(nullptr, *ActorClassPath))
            {
                ActorClass = ClassBP->GeneratedClass;
            }
        }
        if (ActorClass)
        {
            if (UEdGraphPin* ClassPin = Node->GetClassPin())
            {
                const UEdGraphSchema_K2* K2Schema = GetDefault<UEdGraphSchema_K2>();
                K2Schema->TrySetDefaultObject(*ClassPin, ActorClass);
                Node->ReconstructNode();
            }
        }
    }

    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), true);
    Result->SetStringField(TEXT("node_id"), Node->NodeGuid.ToString());
    return Result;
}
TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleGetNodePins(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName, NodeId;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName) || !Params->TryGetStringField(TEXT("node_id"), NodeId))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing blueprint_name or node_id"));
    }
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint not found"));
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No event graph"));

    UEdGraphNode* Target = nullptr;
    for (UEdGraphNode* Node : EventGraph->Nodes)
    {
        if (Node && Node->NodeGuid.ToString() == NodeId) { Target = Node; break; }
    }
    if (!Target) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Node not found"));

    TArray<TSharedPtr<FJsonValue>> PinArray;
    for (UEdGraphPin* Pin : Target->Pins)
    {
        if (!Pin) continue;
        TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
        P->SetStringField(TEXT("name"), Pin->PinName.ToString());
        P->SetStringField(TEXT("direction"), Pin->Direction == EGPD_Input ? TEXT("input") : TEXT("output"));
        P->SetStringField(TEXT("category"), Pin->PinType.PinCategory.ToString());
        P->SetStringField(TEXT("subcategory"), Pin->PinType.PinSubCategory.ToString());
        P->SetStringField(TEXT("default_value"), Pin->DefaultValue);
        if (Pin->DefaultObject) P->SetStringField(TEXT("default_object"), Pin->DefaultObject->GetPathName());
        TArray<TSharedPtr<FJsonValue>> Links;
        for (UEdGraphPin* Linked : Pin->LinkedTo)
        {
            if (!Linked || !Linked->GetOwningNode()) continue;
            TSharedPtr<FJsonObject> L = MakeShared<FJsonObject>();
            L->SetStringField(TEXT("node_id"), Linked->GetOwningNode()->NodeGuid.ToString());
            L->SetStringField(TEXT("pin"), Linked->PinName.ToString());
            L->SetStringField(TEXT("node_title"), Linked->GetOwningNode()->GetNodeTitle(ENodeTitleType::ListView).ToString());
            Links.Add(MakeShared<FJsonValueObject>(L));
        }
        P->SetArrayField(TEXT("linked_to"), Links);
        PinArray.Add(MakeShared<FJsonValueObject>(P));
    }

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), true);
    Result->SetStringField(TEXT("node_id"), NodeId);
    Result->SetStringField(TEXT("title"), Target->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
    Result->SetStringField(TEXT("class"), Target->GetClass()->GetName());
    Result->SetArrayField(TEXT("pins"), PinArray);
    return Result;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleDisconnectPin(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName, NodeId, PinName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName) ||
        !Params->TryGetStringField(TEXT("node_id"), NodeId) ||
        !Params->TryGetStringField(TEXT("pin_name"), PinName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing blueprint_name, node_id, or pin_name"));
    }
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint not found"));
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No event graph"));

    UEdGraphNode* Target = nullptr;
    for (UEdGraphNode* Node : EventGraph->Nodes)
    {
        if (Node && Node->NodeGuid.ToString() == NodeId) { Target = Node; break; }
    }
    if (!Target) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Node not found"));

    UEdGraphPin* Found = nullptr;
    for (UEdGraphPin* Pin : Target->Pins)
    {
        if (Pin && Pin->PinName.ToString().Equals(PinName, ESearchCase::IgnoreCase))
        {
            Found = Pin;
            break;
        }
    }
    if (!Found) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Pin not found"));
    Found->BreakAllPinLinks(true);
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), true);
    Result->SetStringField(TEXT("node_id"), NodeId);
    Result->SetStringField(TEXT("pin_name"), PinName);
    return Result;
}

TSharedPtr<FJsonObject> FUnrealMCPBlueprintNodeCommands::HandleDeleteBlueprintNodes(const TSharedPtr<FJsonObject>& Params)
{
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing blueprint_name"));
    }
    const TArray<TSharedPtr<FJsonValue>>* NodeIds = nullptr;
    if (!Params->TryGetArrayField(TEXT("node_ids"), NodeIds) || !NodeIds || NodeIds->Num() == 0)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing node_ids array"));
    }
    UBlueprint* Blueprint = FUnrealMCPCommonUtils::FindBlueprint(BlueprintName);
    if (!Blueprint) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint not found"));
    UEdGraph* EventGraph = FUnrealMCPCommonUtils::FindOrCreateEventGraph(Blueprint);
    if (!EventGraph) return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No event graph"));

    TSet<FString> Wanted;
    for (const TSharedPtr<FJsonValue>& V : *NodeIds)
    {
        Wanted.Add(V->AsString());
    }

    TArray<UEdGraphNode*> ToDelete;
    for (UEdGraphNode* Node : EventGraph->Nodes)
    {
        if (Node && Wanted.Contains(Node->NodeGuid.ToString()))
        {
            ToDelete.Add(Node);
        }
    }
    for (UEdGraphNode* Node : ToDelete)
    {
        EventGraph->RemoveNode(Node);
    }
    FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("success"), true);
    Result->SetNumberField(TEXT("deleted"), ToDelete.Num());
    return Result;
}
